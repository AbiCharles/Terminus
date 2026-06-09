class StatsController < ApplicationController
  def show
    render json: {
      snapshot_requests: ApiStats.snapshot_requests,
      experiment_requests: ApiStats.experiment_requests
    }
  end
end
