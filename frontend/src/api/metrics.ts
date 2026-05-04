import { api } from "./client";
import type { Metrics } from "./types";

export const metricsApi = {
  get: (days = 7) => api<Metrics>(`/api/v1/metrics?days=${days}`),
};
