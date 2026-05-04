import { api } from "./client";
import type { Killswitch } from "./types";

export const settingsApi = {
  list: () => api<Killswitch[]>("/api/v1/settings/killswitches"),
  set: (scope: string, enabled: boolean, reason?: string) =>
    api<Killswitch>(`/api/v1/settings/killswitches/${encodeURIComponent(scope)}`, {
      method: "PUT",
      body: JSON.stringify({ enabled, reason }),
    }),
};
