Rails.application.routes.draw do
  get "/health", to: "health#show"
  get "/_stats", to: "stats#show"
  get "/experiments", to: "experiments#index"
  get "/experiments/:id", to: "experiments#show", constraints: { id: /[a-z0-9_]+/ }
  get "/experiments/:id/snapshots", to: "experiments#snapshots", constraints: { id: /[a-z0-9_]+/ }
end
