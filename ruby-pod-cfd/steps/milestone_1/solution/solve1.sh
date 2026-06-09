#!/bin/bash
set -euo pipefail

# Milestone 1 oracle: install the complete reference POD CLI at /app/pod_cli.rb
# (hand-rolled Jacobi eigenanalysis, no linear-algebra libraries) and run it. A
# single correct CLI satisfies all three milestones; each milestone's verifier
# exercises the relevant outputs.
/opt/start_api.sh
cat > /app/pod_cli.rb <<'POD_CLI_EOF'
#!/usr/bin/env ruby
# frozen_string_literal: true
#
# POD analysis CLI for the CFD Rails API. Implemented from scratch with no
# linear-algebra libraries: the covariance eigenproblem is solved with a
# hand-rolled cyclic Jacobi rotation sweep.

require "net/http"
require "uri"
require "json"
require "fileutils"

def get_json(base, path)
  uri = URI.join(base, path)
  res = Net::HTTP.get_response(uri)
  raise "GET #{path} -> #{res.code}" unless res.code.to_i == 200
  JSON.parse(res.body)
end

# Fetch all snapshot frames for an experiment, paginated, ordered by frame index.
def fetch_matrix(base, eid, meta)
  frames = {}
  n_pages = meta["n_pages"]
  (1..n_pages).each do |page|
    body = get_json(base, "/experiments/#{eid}/snapshots?page=#{page}")
    body["frames"].each { |f| frames[f["index"]] = f["values"] }
  end
  ordered = frames.keys.sort.map { |i| frames[i] }       # n rows of length m
  # X is m x n: column t is frame t
  m = ordered.first.length
  n = ordered.length
  x = Array.new(m) { |i| Array.new(n) { |t| ordered[t][i] } }
  [x, m, n]
end

def mean_subtract(x, m, n)
  xc = Array.new(m) { Array.new(n, 0.0) }
  mean = Array.new(m, 0.0)
  (0...m).each do |i|
    s = 0.0
    (0...n).each { |t| s += x[i][t] }
    mu = s / n
    mean[i] = mu
    (0...n).each { |t| xc[i][t] = x[i][t] - mu }
  end
  [xc, mean]
end

# C = (1/(n-1)) * Xc^T Xc   (n x n, method of snapshots)
def covariance(xc, m, n)
  c = Array.new(n) { Array.new(n, 0.0) }
  (0...n).each do |a|
    (a...n).each do |b|
      s = 0.0
      (0...m).each { |i| s += xc[i][a] * xc[i][b] }
      v = s / (n - 1)
      c[a][b] = v
      c[b][a] = v
    end
  end
  c
end

# Eigenvalues of a real symmetric matrix via cyclic Jacobi rotations.
def symmetric_eigenvalues(matrix)
  n = matrix.size
  a = matrix.map(&:dup)
  100.times do
    off = 0.0
    (0...n).each { |p| ((p + 1)...n).each { |q| off += a[p][q] * a[p][q] } }
    break if off <= 1e-20
    (0...n).each do |p|
      ((p + 1)...n).each do |q|
        apq = a[p][q]
        next if apq.abs <= 1e-300
        app = a[p][p]
        aqq = a[q][q]
        tau = (aqq - app) / (2.0 * apq)
        t = (tau >= 0 ? 1.0 : -1.0) / (tau.abs + Math.sqrt(tau * tau + 1.0))
        c = 1.0 / Math.sqrt(t * t + 1.0)
        s = t * c
        (0...n).each do |i|
          aip = a[i][p]
          aiq = a[i][q]
          a[i][p] = c * aip - s * aiq
          a[i][q] = s * aip + c * aiq
        end
        (0...n).each do |i|
          api = a[p][i]
          aqi = a[q][i]
          a[p][i] = c * api - s * aqi
          a[q][i] = s * api + c * aqi
        end
      end
    end
  end
  (0...n).map { |i| a[i][i] }
end

def analyze(base, eid, meta, threshold, outdir)
  x, m, n = fetch_matrix(base, eid, meta)
  xc, = mean_subtract(x, m, n)

  # M1 output: assembled-matrix invariants
  frame_norms = (0...n).map { |t| Math.sqrt((0...m).sum { |i| x[i][t]**2 }) }
  frob = Math.sqrt((0...m).sum { |i| (0...n).sum { |t| x[i][t]**2 } })
  dir = File.join(outdir, eid)
  FileUtils.mkdir_p(dir)
  File.write(File.join(dir, "snapshots_meta.json"), JSON.pretty_generate(
    "experiment_id" => eid, "n_dofs" => m, "n_frames" => n,
    "frame_l2_norms" => frame_norms, "frobenius_norm" => frob
  ))

  # M2 output: modal energy
  c = covariance(xc, m, n)
  eig = symmetric_eigenvalues(c).map { |v| v < 0.0 ? 0.0 : v }.sort.reverse
  total = eig.sum
  frac = eig.map { |v| v / total }
  cum = []
  run = 0.0
  frac.each { |f| run += f; cum << run }
  rows = (0...eig.length).map do |k|
    { "mode_index" => k, "eigenvalue" => eig[k], "energy_fraction" => frac[k], "cumulative_fraction" => cum[k] }
  end
  File.write(File.join(dir, "modal_energy.json"), JSON.pretty_generate("experiment_id" => eid, "modes" => rows))
  csv = +"mode_index,eigenvalue,energy_fraction,cumulative_fraction\n"
  rows.each { |r| csv << "#{r['mode_index']},#{r['eigenvalue']},#{r['energy_fraction']},#{r['cumulative_fraction']}\n" }
  File.write(File.join(dir, "modal_energy.csv"), csv)

  # M3 output: selection + reconstruction error
  k = cum.find_index { |c2| c2 >= threshold }
  k = k.nil? ? eig.length : k + 1
  tail = eig[k..].sum
  recon = Math.sqrt(tail / total)
  selected = (0...k).to_a
  File.write(File.join(dir, "report.json"), JSON.pretty_generate(
    "experiment_id" => eid, "energy_threshold" => threshold,
    "n_selected_modes" => k, "selected_mode_indices" => selected,
    "cumulative_at_selected" => cum[k - 1], "reconstruction_error" => recon
  ))
  File.write(File.join(dir, "report.csv"),
             "experiment_id,energy_threshold,n_selected_modes,reconstruction_error\n" \
             "#{eid},#{threshold},#{k},#{recon}\n")
end

def main
  base = "http://localhost:8000"
  threshold = 0.99
  outdir = "/app/output"
  args = ARGV.dup
  until args.empty?
    case args.shift
    when "--base-url" then base = args.shift
    when "--threshold" then threshold = args.shift.to_f
    when "--output-dir" then outdir = args.shift
    end
  end
  index = get_json(base, "/experiments")
  index["experiments"].each do |e|
    next unless e["is_fixture"]
    eid = e["id"]
    meta = get_json(base, "/experiments/#{eid}")
    analyze(base, eid, meta, threshold, outdir)
  end
end

main if __FILE__ == $PROGRAM_NAME
POD_CLI_EOF
ruby /app/pod_cli.rb --base-url http://localhost:8000 --threshold 0.99 --output-dir /app/output
