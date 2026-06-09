class ExperimentsController < ApplicationController
  FIXTURES_DIR = ENV.fetch("CFD_FIXTURES_DIR", "/opt/api/fixtures")

  def index
    render json: JSON.parse(File.read(File.join(FIXTURES_DIR, "index.json")))
  end

  def show
    data = load_experiment(params[:id])
    return render(json: { error: "experiment not found" }, status: :not_found) unless data
    ApiStats.incr_experiment
    render json: data["meta"]
  end

  def snapshots
    data = load_experiment(params[:id])
    return render(json: { error: "experiment not found" }, status: :not_found) unless data
    meta = data["meta"]
    page_size = meta["page_size"]
    n_pages = meta["n_pages"]
    page = (params[:page] || 1).to_i
    if page < 1 || page > n_pages
      return render(json: { error: "page out of range", n_pages: n_pages }, status: :not_found)
    end
    ApiStats.incr_snapshots
    start = (page - 1) * page_size
    frames = data["frames"][start, page_size] || []
    render json: {
      experiment_id: meta["id"],
      page: page,
      page_size: page_size,
      n_pages: n_pages,
      n_frames: meta["n_frames"],
      next_page: (page < n_pages ? page + 1 : nil),
      frames: frames
    }
  end

  private

  def load_experiment(id)
    return nil unless id.to_s.match?(/\A[a-z0-9_]+\z/)
    path = File.join(FIXTURES_DIR, "#{id}.json")
    return nil unless File.exist?(path)
    JSON.parse(File.read(path))
  end
end
