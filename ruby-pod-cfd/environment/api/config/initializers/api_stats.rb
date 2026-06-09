# In-memory request counters so the verifier can confirm the agent used the API.
module ApiStats
  @mutex = Mutex.new
  @snapshot_requests = 0
  @experiment_requests = 0
  class << self
    def incr_snapshots
      @mutex.synchronize { @snapshot_requests += 1 }
    end

    def incr_experiment
      @mutex.synchronize { @experiment_requests += 1 }
    end

    def snapshot_requests
      @mutex.synchronize { @snapshot_requests }
    end

    def experiment_requests
      @mutex.synchronize { @experiment_requests }
    end
  end
end
