require_relative "boot"

require "rails"
require "action_controller/railtie"

module PodApi
  class Application < Rails::Application
    config.load_defaults 7.1
    config.api_only = true
    config.eager_load = false
    config.consider_all_requests_local = true
    config.secret_key_base = "fixture_api_secret_not_sensitive"
    config.logger = Logger.new($stdout)
    config.log_level = :warn
  end
end
