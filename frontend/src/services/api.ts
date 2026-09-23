import type { Explanation, Prediction, Variable } from "../types/api";

async function get<T>(path: string): Promise<T> {
  const url = path.startsWith("/") ? path : `/${path}`;
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const errorBody = (await response.json()) as {
        detail?: string;
        message?: string;
      };
      message = errorBody.detail ?? errorBody.message ?? message;
    } catch {
      // ignore JSON parse errors and fall back to the HTTP status message
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  latest: async (variable: Variable): Promise<Prediction[]> =>
    (
      await get<{ predictions: Prediction[] }>(
        `/forecast/latest?variable=${variable}`,
      )
    ).predictions,
  explanation: (region: string, variable: Variable, lead: number) =>
    get<Explanation>(
      `/explanations/${region}?variable=${variable}&lead_day=${lead}`,
    ),
  model: () =>
    get<{
      model_version: string;
      data_mode: string;
      metrics: Record<string, number>;
    }>("/model/info"),
};
