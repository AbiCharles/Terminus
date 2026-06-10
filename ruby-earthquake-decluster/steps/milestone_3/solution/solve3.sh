#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: write the executable Ruby CLI to /app/quake (sqlite3 gem) and
# exercise the `report` subcommand. Self-contained across milestones.
cat > /app/quake <<'QUAKE_EOF'
#!/usr/bin/env ruby
# frozen_string_literal: true
#
# Earthquake declustering + recurrence analyzer (Ruby).
#
# A SQLite-backed CLI that filters an earthquake catalog, removes aftershocks and
# foreshocks by the Gardner & Knopoff (1974) windowing method, and computes
# recurrence statistics on the DECLUSTERED catalog: the magnitude of completeness
# (Wiemer & Wyss 2000 goodness-of-fit), the Gutenberg-Richter b-value (Aki-Utsu
# MLE with Shi & Bolt 1982 uncertainty), and Poisson exceedance probabilities.
# Data is read only through SQLite queries; output is deterministic CSV/JSON.
# Exit 2 on invalid filters, 3 on insufficient samples.

require 'sqlite3'

DELTA_M = 0.1
GFT_CONFIDENCE = 90.0
MIN_SAMPLE = 30
MIN_BINS_ABOVE_MC = 4
EARTH_RADIUS_KM = 6371.0
DEG2RAD = Math::PI / 180.0
EX_BADFILTER = 2
EX_INSUFFICIENT = 3

def die_usage(msg)
  warn("error: #{msg}")
  exit(EX_BADFILTER)
end

def parse_number(s, flag)
  Float(s)
rescue ArgumentError, TypeError
  die_usage("#{flag} expects a number, got '#{s}'")
end

def parse_filters(argv)
  f = { db_path: '/app/catalog.db', window_years: 50.0 }
  i = 0
  need = lambda do |flag|
    die_usage("#{flag} requires a value") if i + 1 >= argv.length
    i += 1
    argv[i]
  end
  while i < argv.length
    a = argv[i]
    case a
    when '--db' then f[:db_path] = need.call(a)
    when '--region' then f[:region] = need.call(a)
    when '--lat-min' then f[:lat_min] = parse_number(need.call(a), a)
    when '--lat-max' then f[:lat_max] = parse_number(need.call(a), a)
    when '--lon-min' then f[:lon_min] = parse_number(need.call(a), a)
    when '--lon-max' then f[:lon_max] = parse_number(need.call(a), a)
    when '--start' then f[:start] = need.call(a)
    when '--end' then f[:end] = need.call(a)
    when '--depth-min' then f[:depth_min] = parse_number(need.call(a), a)
    when '--depth-max' then f[:depth_max] = parse_number(need.call(a), a)
    when '--mag-min' then f[:mag_min] = parse_number(need.call(a), a)
    when '--mag-max' then f[:mag_max] = parse_number(need.call(a), a)
    when '--out' then f[:out] = need.call(a)
    when '--out-prefix' then f[:out_prefix] = need.call(a)
    when '--targets' then f[:targets] = need.call(a)
    when '--window-years' then f[:window_years] = parse_number(need.call(a), a)
    else die_usage("unknown argument '#{a}'")
    end
    i += 1
  end
  die_usage('lat-min out of range [-90,90]') if f[:lat_min] && (f[:lat_min] < -90.0 || f[:lat_min] > 90.0)
  die_usage('lat-max out of range [-90,90]') if f[:lat_max] && (f[:lat_max] < -90.0 || f[:lat_max] > 90.0)
  die_usage('lon-min out of range [-180,180]') if f[:lon_min] && (f[:lon_min] < -180.0 || f[:lon_min] > 180.0)
  die_usage('lon-max out of range [-180,180]') if f[:lon_max] && (f[:lon_max] < -180.0 || f[:lon_max] > 180.0)
  die_usage('lat-min > lat-max') if f[:lat_min] && f[:lat_max] && f[:lat_min] > f[:lat_max]
  die_usage('lon-min > lon-max') if f[:lon_min] && f[:lon_max] && f[:lon_min] > f[:lon_max]
  die_usage('depth-min > depth-max') if f[:depth_min] && f[:depth_max] && f[:depth_min] > f[:depth_max]
  die_usage('mag-min > mag-max') if f[:mag_min] && f[:mag_max] && f[:mag_min] > f[:mag_max]
  die_usage('start > end') if f[:start] && f[:end] && f[:start] > f[:end]
  die_usage('window-years must be positive') if f[:window_years] <= 0.0
  f
end

def where_clause(f)
  clauses = ['1=1']
  params = []
  if f[:region] then clauses << 'region = ?'; params << f[:region] end
  [['latitude', :lat_min, '>='], ['latitude', :lat_max, '<='],
   ['longitude', :lon_min, '>='], ['longitude', :lon_max, '<='],
   ['time', :start, '>='], ['time', :end, '<='],
   ['depth_km', :depth_min, '>='], ['depth_km', :depth_max, '<='],
   ['magnitude', :mag_min, '>='], ['magnitude', :mag_max, '<=']].each do |col, key, op|
    next unless f.key?(key)

    clauses << "#{col} #{op} ?"
    params << f[key]
  end
  [' WHERE ' + clauses.join(' AND '), params]
end

def open_db(f)
  SQLite3::Database.new(f[:db_path], readonly: true)
rescue SQLite3::Exception => e
  die_usage("cannot open database '#{f[:db_path]}': #{e.message}")
end

def load_events(db, f)
  where, params = where_clause(f)
  sql = 'SELECT id, time, latitude, longitude, depth_km, magnitude, region, julianday(time)' \
        " FROM events#{where} ORDER BY time ASC, id ASC"
  db.execute(sql, params).map do |r|
    { id: r[0], time: r[1], lat: r[2], lon: r[3], depth: r[4], mag: r[5], region: r[6], jd: r[7] }
  end
end

def csv_row(e)
  format("%d,%s,%.4f,%.4f,%.2f,%.1f,%s\n", e[:id], e[:time], e[:lat], e[:lon], e[:depth], e[:mag], e[:region])
end

def cmd_query(f)
  die_usage('query requires --out') unless f[:out]
  events = load_events(open_db(f), f)
  File.open(f[:out], 'w') do |out|
    out.write("id,time,latitude,longitude,depth_km,magnitude,region\n")
    events.each { |e| out.write(csv_row(e)) }
  end
  0
end

# ---- Gardner-Knopoff declustering ----
def haversine_km(la1, lo1, la2, lo2)
  p1 = la1 * DEG2RAD
  p2 = la2 * DEG2RAD
  dphi = (la2 - la1) * DEG2RAD
  dlmb = (lo2 - lo1) * DEG2RAD
  a = Math.sin(dphi / 2.0)**2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dlmb / 2.0)**2
  a = 1.0 if a > 1.0
  2.0 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a))
end

def gk_decluster(events)
  n = events.length
  removed = Array.new(n, false)
  order = (0...n).sort_by { |i| [-events[i][:mag], events[i][:jd], events[i][:id]] }
  order.each do |i|
    next if removed[i]

    ei = events[i]
    m = ei[:mag]
    l = 10.0**(0.1238 * m + 0.983)
    t = m >= 6.5 ? 10.0**(0.5409 * m - 0.547) : 10.0**(0.032 * m + 2.7389)
    (0...n).each do |j|
      next if j == i || removed[j]

      ej = events[j]
      next unless (ej[:jd] - ei[:jd]).abs <= t

      removed[j] = true if haversine_km(ei[:lat], ei[:lon], ej[:lat], ej[:lon]) <= l
    end
  end
  (0...n).reject { |i| removed[i] }.map { |i| events[i] }  # preserves (time, id) order
end

def cmd_decluster(f)
  die_usage('decluster requires --out') unless f[:out]
  events = load_events(open_db(f), f)
  mains = events.empty? ? [] : gk_decluster(events)
  File.open(f[:out], 'w') do |out|
    out.write("id,time,latitude,longitude,depth_km,magnitude,region\n")
    mains.each { |e| out.write(csv_row(e)) }
  end
  0
end

# ---- statistics on the declustered catalog ----
def bin_index(m)
  (m / DELTA_M + 0.5).floor
end

def gft_mc(mags)
  return nil if mags.empty?

  bins = mags.map { |m| bin_index(m) }
  bmin = bins.min
  bmax = bins.max
  nbins = bmax - bmin + 1
  return nil if nbins < MIN_BINS_ABOVE_MC

  hist = Array.new(nbins, 0)
  bins.each { |b| hist[b - bmin] += 1 }
  best_r = -1e9
  best_mc = nil
  (0...(nbins - (MIN_BINS_ABOVE_MC - 1))).each do |c|
    mc = (bmin + c) * DELTA_M
    sample = mags.select { |m| bin_index(m) >= bmin + c }
    next if sample.length < MIN_SAMPLE

    mean = sample.sum / sample.length
    denom = mean - (mc - DELTA_M / 2.0)
    next if denom <= 0.0

    b = Math.log10(Math::E) / denom
    a = Math.log10(sample.length) + b * mc
    abs_sum = 0.0
    obs_sum = 0.0
    (c...nbins).each do |k|
      center = (bmin + k) * DELTA_M
      obs_cum = hist[k...nbins].sum
      pred_cum = 10.0**(a - b * center)
      abs_sum += (obs_cum - pred_cum).abs
      obs_sum += obs_cum
    end
    r = 100.0 * (1.0 - abs_sum / obs_sum)
    if r > best_r
      best_r = r
      best_mc = mc
    end
    return [mc, r] if r >= GFT_CONFIDENCE
  end
  best_mc.nil? ? nil : [best_mc, best_r]
end

def grfit(mags)
  res = gft_mc(mags)
  return nil if res.nil?

  mc, = res
  cmin = bin_index(mc)
  above = mags.select { |m| bin_index(m) >= cmin }
  return nil if above.length < MIN_SAMPLE

  mean = above.sum / above.length
  denom = mean - (mc - DELTA_M / 2.0)
  return nil if denom <= 0.0

  b = Math.log10(Math::E) / denom
  var = above.map { |m| (m - mean)**2 }.sum / (above.length.to_f * (above.length - 1))
  { mc: mc, n_above_mc: above.length, b_value: b,
    b_uncertainty: 2.30 * b * b * Math.sqrt(var), a_value: Math.log10(above.length) + b * mc }
end

def declustered_stats(f)
  events = load_events(open_db(f), f)
  raise 'no events' if events.empty?

  mains = gk_decluster(events)
  raise 'no events' if mains.empty?

  mags = mains.map { |e| e[:mag] }.sort
  res = gft_mc(mags)
  raise 'insufficient' if res.nil?

  mc, gft_r = res
  cmin = bin_index(mc)
  above = mags.select { |m| bin_index(m) >= cmin }
  raise 'insufficient' if above.length < MIN_SAMPLE

  mean = above.sum / above.length
  denom = mean - (mc - DELTA_M / 2.0)
  raise 'insufficient' if denom <= 0.0

  b = Math.log10(Math::E) / denom
  var = above.map { |m| (m - mean)**2 }.sum / (above.length.to_f * (above.length - 1))
  jds = mains.map { |e| e[:jd] }
  {
    n_total: mains.length, n_above_mc: above.length, mc: mc, b_value: b,
    b_uncertainty: 2.30 * b * b * Math.sqrt(var), a_value: Math.log10(above.length) + b * mc,
    catalog_years: (jds.max - jds.min) / 365.25,
    mag_min: mags.min, mag_max: mags.max, mains: mains, mags: mags
  }
end

def stats_json(s)
  +"{\n" \
    "  \"completeness_method\": \"goodness_of_fit\",\n" \
    "  \"gft_confidence\": #{format('%.1f', GFT_CONFIDENCE)},\n" \
    "  \"delta_m\": #{format('%.1f', DELTA_M)},\n" \
    "  \"n_total\": #{s[:n_total]},\n" \
    "  \"n_above_mc\": #{s[:n_above_mc]},\n" \
    "  \"mc\": #{format('%.1f', s[:mc])},\n" \
    "  \"b_value\": #{format('%.4f', s[:b_value])},\n" \
    "  \"b_uncertainty\": #{format('%.4f', s[:b_uncertainty])},\n" \
    "  \"a_value\": #{format('%.4f', s[:a_value])},\n" \
    "  \"catalog_years\": #{format('%.4f', s[:catalog_years])},\n" \
    "  \"magnitude_range\": {\"min\": #{format('%.1f', s[:mag_min])}, \"max\": #{format('%.1f', s[:mag_max])}}\n}\n"
end

def cmd_stats(f)
  s = begin
    declustered_stats(f)
  rescue StandardError
    warn('error: insufficient sample')
    exit(EX_INSUFFICIENT)
  end
  if f[:out]
    File.write(f[:out], stats_json(s))
  else
    print stats_json(s)
  end
  0
end

def parse_targets(spec)
  spec.split(',').map { |t| Float(t) rescue die_usage('invalid --targets value') }
end

def cmd_report(f)
  die_usage('report requires --out-prefix') unless f[:out_prefix]
  s = begin
    declustered_stats(f)
  rescue StandardError
    warn('error: insufficient sample')
    exit(EX_INSUFFICIENT)
  end
  bins = s[:mags].map { |m| bin_index(m) }
  bmin = bins.min
  bmax = bins.max
  nbins = bmax - bmin + 1
  hist = Array.new(nbins, 0)
  bins.each { |b| hist[b - bmin] += 1 }
  File.open("#{f[:out_prefix]}_fmd.csv", 'w') do |fmd|
    fmd.write("magnitude,count,cumulative_count\n")
    (0...nbins).each do |k|
      center = (bmin + k) * DELTA_M
      cum = hist[k...nbins].sum
      fmd.write(format("%.1f,%d,%d\n", center, hist[k], cum))
    end
  end
  targets = f[:targets] ? parse_targets(f[:targets]) : [5.0, 6.0, 7.0]
  exc = targets.map do |m|
    expected = 10.0**(s[:a_value] - s[:b_value] * m)
    rate = expected / s[:catalog_years]
    prob = 1.0 - Math.exp(-rate * f[:window_years])
    format("    {\"magnitude\": %.1f, \"annual_rate\": %.6f, \"exceedance_probability\": %.6f}", m, rate, prob)
  end
  by = Hash.new { |h, k| h[k] = [] }
  s[:mains].each { |e| by[e[:region]] << e }
  per = []
  by.keys.sort.each do |region|
    fit = grfit(by[region].map { |e| e[:mag] }.sort)
    next if fit.nil?

    per << format("    {\"region\": \"%s\", \"n_total\": %d, \"n_above_mc\": %d, \"mc\": %.1f, " \
                  "\"b_value\": %.4f, \"b_uncertainty\": %.4f, \"a_value\": %.4f}",
                  region, by[region].length, fit[:n_above_mc], fit[:mc],
                  fit[:b_value], fit[:b_uncertainty], fit[:a_value])
  end
  summary = +"{\n" \
    "  \"completeness_method\": \"goodness_of_fit\",\n" \
    "  \"gft_confidence\": #{format('%.1f', GFT_CONFIDENCE)},\n" \
    "  \"delta_m\": #{format('%.1f', DELTA_M)},\n" \
    "  \"n_total\": #{s[:n_total]},\n" \
    "  \"n_above_mc\": #{s[:n_above_mc]},\n" \
    "  \"mc\": #{format('%.1f', s[:mc])},\n" \
    "  \"b_value\": #{format('%.4f', s[:b_value])},\n" \
    "  \"b_uncertainty\": #{format('%.4f', s[:b_uncertainty])},\n" \
    "  \"a_value\": #{format('%.4f', s[:a_value])},\n" \
    "  \"catalog_years\": #{format('%.4f', s[:catalog_years])},\n" \
    "  \"window_years\": #{format('%.1f', f[:window_years])},\n" \
    "  \"magnitude_range\": {\"min\": #{format('%.1f', s[:mag_min])}, \"max\": #{format('%.1f', s[:mag_max])}},\n" \
    "  \"exceedance\": [\n#{exc.join(",\n")}\n  ],\n" \
    "  \"per_region\": [\n#{per.join(",\n")}\n  ]\n}\n"
  File.write("#{f[:out_prefix]}_summary.json", summary)
  0
end

def main(argv)
  if argv.empty?
    warn('usage: quake <query|decluster|stats|report> [filters]')
    exit(EX_BADFILTER)
  end
  cmd = argv[0]
  f = parse_filters(argv[1..])
  case cmd
  when 'query' then exit(cmd_query(f))
  when 'decluster' then exit(cmd_decluster(f))
  when 'stats' then exit(cmd_stats(f))
  when 'report' then exit(cmd_report(f))
  else
    warn("error: unknown command '#{cmd}'")
    exit(EX_BADFILTER)
  end
end

main(ARGV)
QUAKE_EOF
chmod +x /app/quake
/app/quake report --db /app/catalog.db --region Cascadia --out-prefix /app/report
echo " wrote /app/report_*"
