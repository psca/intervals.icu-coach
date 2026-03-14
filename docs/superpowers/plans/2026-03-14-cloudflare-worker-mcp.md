# Cloudflare Worker MCP Server Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a TypeScript Cloudflare Worker that implements the full intervals.icu MCP server, replacing the Python fork and `weather.py` with a zero-local-infrastructure deployment.

**Architecture:** A stateless CF Worker handles MCP Streamable HTTP requests, initialising an `IntervalsClient` per request from CF Secrets, and dispatching to 12 typed tools across activities, events, wellness, and a new server-side weather pipeline. The weather pipeline fetches GPS streams from intervals.icu and calls Open-Meteo directly, removing the need for any client-side script.

**Tech Stack:** TypeScript, Cloudflare Workers, `@modelcontextprotocol/sdk` ≥1.10.0, `wrangler`, `vitest`

**Spec:** `../intervals.icu-coach/docs/superpowers/specs/2026-03-14-cloudflare-worker-mcp-design.md`
**Reference Python tools:** `../intervals-mcp-server/src/intervals_mcp_server/tools/`
**Reference weather script:** `../intervals.icu-coach/skills/triathlon-training/scripts/weather.py`

---

## Chunk 1: Foundation — Scaffold, Client, Formatting

### File Map

| File | Responsibility |
|---|---|
| `src/index.ts` | Worker entry point — MCP server init, tool registration, request routing |
| `src/client.ts` | intervals.icu HTTP client — auth injection, GET/POST/PUT/DELETE |
| `src/formatting.ts` | Pure string formatters — activity, event, wellness, intervals |
| `test/client.test.ts` | Unit tests for auth header and error handling |
| `test/formatting.test.ts` | Unit tests for all formatting functions |
| `wrangler.toml` | CF Worker config |
| `package.json` | Dependencies |
| `tsconfig.json` | TypeScript config |

---

### Task 1: Scaffold the Wrangler TypeScript project

**Files:**
- Create: `wrangler.toml`
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `src/index.ts` (stub)

- [ ] **Step 1: Initialise the project**

  ```bash
  cd /path/to/intervals.icu-server
  npm create cloudflare@latest . -- --type hello-world --lang ts --no-deploy
  ```

  This creates `wrangler.toml`, `package.json`, `tsconfig.json`, and `src/index.ts`.

- [ ] **Step 2: Install dependencies**

  ```bash
  npm install @modelcontextprotocol/sdk@latest
  npm install --save-dev vitest
  ```

  Verify `@modelcontextprotocol/sdk` version is ≥1.10.0:
  ```bash
  cat node_modules/@modelcontextprotocol/sdk/package.json | grep '"version"'
  ```

- [ ] **Step 3: Update `wrangler.toml`**

  Replace the generated file with:
  ```toml
  name = "intervals-mcp"
  main = "src/index.ts"
  compatibility_date = "2026-01-01"

  # Secrets set via:
  #   wrangler secret put API_KEY
  #   wrangler secret put ATHLETE_ID
  ```

- [ ] **Step 4: Add vitest config to `package.json`**

  Add to `package.json` scripts section:
  ```json
  "test": "vitest run",
  "test:watch": "vitest"
  ```

  > **Vitest pool note:** All unit tests run in the default Node pool — correct for testing pure functions and mocked fetch. Do NOT install `@cloudflare/vitest-pool-workers`; that's only needed for CF runtime features (KV, Durable Objects). Integration testing is done via `wrangler dev` smoke tests.

- [ ] **Step 4b: Verify MCP SDK import paths**

  ```bash
  node -e "require('@modelcontextprotocol/sdk/server/mcp.js'); console.log('ok')"
  node -e "require('@modelcontextprotocol/sdk/server/streamableHttp.js'); console.log('ok')"
  ```
  Expected: `ok` for both. If either fails, check the installed version (`npm list @modelcontextprotocol/sdk`) and upgrade to ≥1.10.0.

- [ ] **Step 5: Verify scaffold compiles**

  ```bash
  npx tsc --noEmit
  ```
  Expected: no errors (may warn about unused imports in generated stub — fine).

- [ ] **Step 6: Commit**

  ```bash
  git init   # if not already a git repo
  git add .
  git commit -m "feat: scaffold CF Worker TypeScript project"
  ```

---

### Task 2: intervals.icu client

**Files:**
- Create: `src/client.ts`
- Create: `test/client.test.ts`

- [ ] **Step 1: Write failing tests for auth header construction**

  Create `test/client.test.ts`:

  ```typescript
  import { describe, it, expect, vi, beforeEach } from "vitest";
  import { IntervalsClient } from "../src/client";

  describe("IntervalsClient", () => {
    describe("auth header", () => {
      it("constructs Basic auth with API_KEY username", () => {
        const client = new IntervalsClient("mysecretkey", "i12345");
        const expected = "Basic " + btoa("API_KEY:mysecretkey");
        expect(client.authHeader).toBe(expected);
      });

      it("exposes athleteId", () => {
        const client = new IntervalsClient("key", "i99999");
        expect(client.athleteId).toBe("i99999");
      });
    });

    describe("GET request", () => {
      beforeEach(() => {
        vi.stubGlobal("fetch", vi.fn());
      });

      it("appends query params to URL", async () => {
        const mockFetch = vi.mocked(fetch);
        mockFetch.mockResolvedValueOnce(
          new Response(JSON.stringify([{ id: "a1" }]), { status: 200 })
        );

        const client = new IntervalsClient("key", "i12345");
        await client.get("/athlete/i12345/activities", { oldest: "2026-01-01" });

        const calledUrl = mockFetch.mock.calls[0][0] as string;
        expect(calledUrl).toContain("oldest=2026-01-01");
        expect(calledUrl).toContain("https://api.intervals.icu/api/v1");
      });

      it("throws on non-200 response", async () => {
        vi.mocked(fetch).mockResolvedValueOnce(
          new Response("Unauthorized", { status: 401 })
        );

        const client = new IntervalsClient("bad-key", "i12345");
        await expect(client.get("/athlete/i12345/activities")).rejects.toThrow("401");
      });
    });

    describe("POST request", () => {
      it("sends JSON body with Content-Type header", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(
          new Response(JSON.stringify({ id: "e1" }), { status: 200 })
        ));

        const client = new IntervalsClient("key", "i12345");
        await client.post("/athlete/i12345/events", { name: "Test Ride" });

        const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
        expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
        expect(init.body).toBe(JSON.stringify({ name: "Test Ride" }));
      });
    });

    describe("DELETE request", () => {
      it("sends DELETE method with no body", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(
          new Response(null, { status: 204 })
        ));

        const client = new IntervalsClient("key", "i12345");
        await client.delete("/athlete/i12345/events/e1");

        const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
        expect(init.method).toBe("DELETE");
        expect(init.body).toBeUndefined();
      });
    });
  });
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  npm test
  ```
  Expected: `Cannot find module '../src/client'`

- [ ] **Step 3: Implement `src/client.ts`**

  ```typescript
  export class IntervalsClient {
    private static readonly BASE_URL = "https://api.intervals.icu/api/v1";
    readonly authHeader: string;
    readonly athleteId: string;

    constructor(apiKey: string, athleteId: string) {
      this.authHeader = "Basic " + btoa(`API_KEY:${apiKey}`);
      this.athleteId = athleteId;
    }

    async get<T>(path: string, params?: Record<string, string>): Promise<T> {
      const url = new URL(IntervalsClient.BASE_URL + path);
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          url.searchParams.set(k, v);
        }
      }
      const res = await fetch(url.toString(), {
        headers: { Authorization: this.authHeader, Accept: "application/json" },
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      return res.json() as Promise<T>;
    }

    async post<T>(path: string, body: unknown): Promise<T> {
      const res = await fetch(IntervalsClient.BASE_URL + path, {
        method: "POST",
        headers: {
          Authorization: this.authHeader,
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      return res.json() as Promise<T>;
    }

    async put<T>(path: string, body: unknown): Promise<T> {
      const res = await fetch(IntervalsClient.BASE_URL + path, {
        method: "PUT",
        headers: {
          Authorization: this.authHeader,
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      return res.json() as Promise<T>;
    }

    async delete(path: string): Promise<void> {
      const res = await fetch(IntervalsClient.BASE_URL + path, {
        method: "DELETE",
        headers: { Authorization: this.authHeader },
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
    }
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  npm test
  ```
  Expected: `8 passed`

- [ ] **Step 5: Commit**

  ```bash
  git add src/client.ts test/client.test.ts
  git commit -m "feat: intervals.icu HTTP client with Basic auth"
  ```

---

### Task 3: Formatting utilities

Port from: `../intervals-mcp-server/src/intervals_mcp_server/utils/formatting.py`

**Files:**
- Create: `src/formatting.ts`
- Create: `test/formatting.test.ts`

- [ ] **Step 1: Write failing tests**

  Create `test/formatting.test.ts`:

  ```typescript
  import { describe, it, expect } from "vitest";
  import {
    formatActivitySummary,
    formatIntervals,
    formatEventSummary,
    formatEventDetails,
    formatWellnessEntry,
  } from "../src/formatting";

  describe("formatActivitySummary", () => {
    it("includes activity name and type", () => {
      const result = formatActivitySummary({
        name: "Morning Ride",
        type: "Ride",
        start_date_local: "2026-03-10T09:00:00",
        distance: 50000,
        moving_time: 5400,
        icu_training_load: 65,
      });
      expect(result).toContain("Morning Ride");
      expect(result).toContain("Ride");
    });

    it("handles missing optional fields gracefully", () => {
      const result = formatActivitySummary({ name: "Unnamed", type: "Run" });
      expect(result).toContain("Unnamed");
    });
  });

  describe("formatWellnessEntry", () => {
    it("includes date and HRV if present", () => {
      const result = formatWellnessEntry({
        date: "2026-03-10",
        hrv: 52,
        restingHR: 48,
      });
      expect(result).toContain("2026-03-10");
      expect(result).toContain("52");
    });
  });

  describe("formatEventSummary", () => {
    it("includes event name and date", () => {
      const result = formatEventSummary({
        name: "Easy Run",
        start_date_local: "2026-03-15T07:00:00",
        type: "Run",
      });
      expect(result).toContain("Easy Run");
      expect(result).toContain("2026-03-15");
    });
  });
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  npm test
  ```
  Expected: `Cannot find module '../src/formatting'`

- [ ] **Step 3: Implement `src/formatting.ts`**

  Complete port of `formatting.py`. Every field from the Python source is included below.

  ```typescript
  // src/formatting.ts
  // Complete port of intervals-mcp-server/src/intervals_mcp_server/utils/formatting.py

  type R = Record<string, unknown>;

  function get(obj: R, ...keys: string[]): unknown {
    for (const k of keys) { if (obj[k] != null) return obj[k]; }
    return "N/A";
  }

  export function formatActivitySummary(a: R): string {
    // Port of format_activity_summary()
    let startTime = String(get(a, "startTime", "start_date_local", "start_date"));
    if (startTime.length > 10) {
      try {
        const dt = new Date(startTime);
        startTime = dt.toISOString().replace("T", " ").slice(0, 19);
      } catch { /* keep as-is */ }
    }

    let rpe: string = String(get(a, "perceived_exertion", "icu_rpe"));
    if (rpe !== "N/A" && !isNaN(Number(rpe))) rpe = `${rpe}/10`;

    let feel: string = String(get(a, "feel"));
    if (feel !== "N/A" && !isNaN(Number(feel))) feel = `${feel}/5`;

    return `
Activity: ${get(a, "name") ?? "Unnamed"}
ID: ${get(a, "id")}
Type: ${get(a, "type")}
Date: ${startTime}
Description: ${get(a, "description")}
Distance: ${get(a, "distance")} meters
Duration: ${get(a, "duration", "elapsed_time")} seconds
Moving Time: ${get(a, "moving_time")} seconds
Elevation Gain: ${get(a, "elevationGain", "total_elevation_gain")} meters
Elevation Loss: ${get(a, "total_elevation_loss")} meters

Power Data:
Average Power: ${get(a, "avgPower", "icu_average_watts", "average_watts")} watts
Weighted Avg Power: ${get(a, "icu_weighted_avg_watts")} watts
Training Load: ${get(a, "trainingLoad", "icu_training_load")}
FTP: ${get(a, "icu_ftp")} watts
Kilojoules: ${get(a, "icu_joules")}
Intensity: ${get(a, "icu_intensity")}
Power:HR Ratio: ${get(a, "icu_power_hr")}
Variability Index: ${get(a, "icu_variability_index")}

Heart Rate Data:
Average Heart Rate: ${get(a, "avgHr", "average_heartrate")} bpm
Max Heart Rate: ${get(a, "max_heartrate")} bpm
LTHR: ${get(a, "lthr")} bpm
Resting HR: ${get(a, "icu_resting_hr")} bpm
Decoupling: ${get(a, "decoupling")}

Other Metrics:
Cadence: ${get(a, "average_cadence")} rpm
Calories: ${get(a, "calories")}
Average Speed: ${get(a, "average_speed")} m/s
Max Speed: ${get(a, "max_speed")} m/s
Average Stride: ${get(a, "average_stride")}
L/R Balance: ${get(a, "avg_lr_balance")}
Weight: ${get(a, "icu_weight")} kg
RPE: ${rpe}
Session RPE: ${get(a, "session_rpe")}
Feel: ${feel}

Environment:
Trainer: ${get(a, "trainer")}
Average Temp: ${get(a, "average_temp")}°C
Min Temp: ${get(a, "min_temp")}°C
Max Temp: ${get(a, "max_temp")}°C
Avg Wind Speed: ${get(a, "average_wind_speed")} km/h
Headwind %: ${get(a, "headwind_percent")}%
Tailwind %: ${get(a, "tailwind_percent")}%

Training Metrics:
Fitness (CTL): ${get(a, "icu_ctl")}
Fatigue (ATL): ${get(a, "icu_atl")}
TRIMP: ${get(a, "trimp")}
Polarization Index: ${get(a, "polarization_index")}
Power Load: ${get(a, "power_load")}
HR Load: ${get(a, "hr_load")}
Pace Load: ${get(a, "pace_load")}
Efficiency Factor: ${get(a, "icu_efficiency_factor")}

Device Info:
Device: ${get(a, "device_name")}
Power Meter: ${get(a, "power_meter")}
File Type: ${get(a, "file_type")}
`.trim();
  }

  export function formatIntervals(data: R): string {
    // Port of format_intervals()
    let result = `Intervals Analysis:\n\nID: ${get(data, "id")}\nAnalyzed: ${get(data, "analyzed")}\n\n`;

    const intervals = (data.icu_intervals as R[]) ?? [];
    if (intervals.length) {
      result += "Individual Intervals:\n\n";
      for (let i = 0; i < intervals.length; i++) {
        const iv = intervals[i];
        result += `[${i + 1}] ${iv.label ?? `Interval ${i + 1}`} (${get(iv, "type")})\n`;
        result += `Duration: ${get(iv, "elapsed_time")} seconds (moving: ${get(iv, "moving_time")} seconds)\n`;
        result += `Distance: ${get(iv, "distance")} meters\n`;
        result += `Start-End Indices: ${get(iv, "start_index")}-${get(iv, "end_index")}\n\n`;
        result += `Power Metrics:\n`;
        result += `  Average Power: ${get(iv, "average_watts")} watts (${get(iv, "average_watts_kg")} W/kg)\n`;
        result += `  Max Power: ${get(iv, "max_watts")} watts (${get(iv, "max_watts_kg")} W/kg)\n`;
        result += `  Weighted Avg Power: ${get(iv, "weighted_average_watts")} watts\n`;
        result += `  Intensity: ${get(iv, "intensity")}\n`;
        result += `  Training Load: ${get(iv, "training_load")}\n`;
        result += `  Joules: ${get(iv, "joules")}\n`;
        result += `  Joules > FTP: ${get(iv, "joules_above_ftp")}\n`;
        result += `  Power Zone: ${get(iv, "zone")} (${get(iv, "zone_min_watts")}-${get(iv, "zone_max_watts")} watts)\n`;
        result += `  W' Balance: Start ${get(iv, "wbal_start")}, End ${get(iv, "wbal_end")}\n`;
        result += `  L/R Balance: ${get(iv, "avg_lr_balance")}\n`;
        result += `  Variability: ${get(iv, "w5s_variability")}\n`;
        result += `  Torque: Avg ${get(iv, "average_torque")}, Min ${get(iv, "min_torque")}, Max ${get(iv, "max_torque")}\n\n`;
        result += `Heart Rate & Metabolic:\n`;
        result += `  Heart Rate: Avg ${get(iv, "average_heartrate")}, Min ${get(iv, "min_heartrate")}, Max ${get(iv, "max_heartrate")} bpm\n`;
        result += `  Decoupling: ${get(iv, "decoupling")}\n`;
        result += `  DFA α1: ${get(iv, "average_dfa_a1")}\n`;
        result += `  Respiration: ${get(iv, "average_respiration")} breaths/min\n`;
        result += `  EPOC: ${get(iv, "average_epoc")}\n`;
        result += `  SmO2: ${get(iv, "average_smo2")}% / ${get(iv, "average_smo2_2")}%\n`;
        result += `  THb: ${get(iv, "average_thb")} / ${get(iv, "average_thb_2")}\n\n`;
        result += `Speed & Cadence:\n`;
        result += `  Speed: Avg ${get(iv, "average_speed")}, Min ${get(iv, "min_speed")}, Max ${get(iv, "max_speed")} m/s\n`;
        result += `  GAP: ${get(iv, "gap")} m/s\n`;
        result += `  Cadence: Avg ${get(iv, "average_cadence")}, Min ${get(iv, "min_cadence")}, Max ${get(iv, "max_cadence")} rpm\n`;
        result += `  Stride: ${get(iv, "average_stride")}\n\n`;
        result += `Elevation & Environment:\n`;
        result += `  Elevation Gain: ${get(iv, "total_elevation_gain")} meters\n`;
        result += `  Altitude: Min ${get(iv, "min_altitude")}, Max ${get(iv, "max_altitude")} meters\n`;
        result += `  Gradient: ${get(iv, "average_gradient")}%\n`;
        result += `  Temperature: ${get(iv, "average_temp")}°C (Weather: ${get(iv, "average_weather_temp")}°C, Feels like: ${get(iv, "average_feels_like")}°C)\n`;
        result += `  Wind: Speed ${get(iv, "average_wind_speed")} km/h, Gust ${get(iv, "average_wind_gust")} km/h, Direction ${get(iv, "prevailing_wind_deg")}°\n`;
        result += `  Headwind: ${get(iv, "headwind_percent")}%, Tailwind: ${get(iv, "tailwind_percent")}%\n\n`;
      }
    }

    const groups = (data.icu_groups as R[]) ?? [];
    if (groups.length) {
      result += "Interval Groups:\n\n";
      for (let i = 0; i < groups.length; i++) {
        const g = groups[i];
        result += `Group: ${get(g, "id")} (Contains ${get(g, "count")} intervals)\n`;
        result += `Duration: ${get(g, "elapsed_time")} seconds (moving: ${get(g, "moving_time")} seconds)\n`;
        result += `Distance: ${get(g, "distance")} meters\n`;
        result += `Power: Avg ${get(g, "average_watts")} watts (${get(g, "average_watts_kg")} W/kg), Max ${get(g, "max_watts")} watts\n`;
        result += `W. Avg Power: ${get(g, "weighted_average_watts")} watts, Intensity: ${get(g, "intensity")}\n`;
        result += `Heart Rate: Avg ${get(g, "average_heartrate")}, Max ${get(g, "max_heartrate")} bpm\n`;
        result += `Speed: Avg ${get(g, "average_speed")}, Max ${get(g, "max_speed")} m/s\n`;
        result += `Cadence: Avg ${get(g, "average_cadence")}, Max ${get(g, "max_cadence")} rpm\n\n`;
      }
    }
    return result;
  }

  export function formatEventSummary(e: R): string {
    // Port of format_event_summary()
    const eventDate = get(e, "start_date_local", "date");
    const eventType = e.workout ? "Workout" : e.race ? "Race" : "Other";
    return `Date: ${eventDate}\nID: ${get(e, "id")}\nType: ${eventType}\nName: ${get(e, "name") ?? "Unnamed"}\nDescription: ${get(e, "description")}`;
  }

  export function formatEventDetails(e: R): string {
    // Port of format_event_details()
    let out = `Event Details:\n\nID: ${get(e, "id")}\nDate: ${get(e, "date")}\nName: ${get(e, "name") ?? "Unnamed"}\nDescription: ${get(e, "description")}`;

    const workout = e.workout as R | undefined;
    if (workout) {
      out += `\n\nWorkout Information:\nWorkout ID: ${get(workout, "id")}\nSport: ${get(workout, "sport")}\nDuration: ${get(workout, "duration")} seconds\nTSS: ${get(workout, "tss")}`;
      const ivs = workout.intervals as unknown[] | undefined;
      if (Array.isArray(ivs)) out += `\nIntervals: ${ivs.length}`;
    }

    if (e.race) {
      out += `\n\nRace Information:\nPriority: ${get(e, "priority")}\nResult: ${get(e, "result")}`;
    }

    const cal = e.calendar as R | undefined;
    if (cal) out += `\n\nCalendar: ${get(cal, "name")}`;

    return out;
  }

  export function formatWellnessEntry(w: R): string {
    // Port of format_wellness_entry() — all sections
    const lines: string[] = ["Wellness Data:", `Date: ${get(w, "id", "date")}`, ""];

    // Training metrics
    const tm: string[] = [];
    for (const [k, label] of [["ctl","Fitness (CTL)"],["atl","Fatigue (ATL)"],["rampRate","Ramp Rate"],["ctlLoad","CTL Load"],["atlLoad","ATL Load"]] as [string,string][]) {
      if (w[k] != null) tm.push(`- ${label}: ${w[k]}`);
    }
    if (tm.length) { lines.push("Training Metrics:", ...tm, ""); }

    // Sport-specific eFTP
    const si = w.sportInfo as R[] | undefined;
    if (Array.isArray(si) && si.length) {
      const slines = si.filter(s => s.eftp != null).map(s => `- ${s.type}: eFTP = ${s.eftp}`);
      if (slines.length) lines.push("Sport-Specific Info:", ...slines, "");
    }

    // Vital signs
    const vs: string[] = [];
    for (const [k, label, unit] of [
      ["weight","Weight","kg"],["restingHR","Resting HR","bpm"],["hrv","HRV",""],
      ["hrvSDNN","HRV SDNN",""],["avgSleepingHR","Average Sleeping HR","bpm"],
      ["spO2","SpO2","%"],["respiration","Respiration","breaths/min"],
      ["bloodGlucose","Blood Glucose","mmol/L"],["lactate","Lactate","mmol/L"],
      ["vo2max","VO2 Max","ml/kg/min"],["bodyFat","Body Fat","%"],
      ["abdomen","Abdomen","cm"],["baevskySI","Baevsky Stress Index",""],
    ] as [string,string,string][]) {
      if (w[k] != null) {
        if (k === "restingHR" && w.systolic != null && w.diastolic != null) {
          vs.push(`- Blood Pressure: ${w.systolic}/${w.diastolic} mmHg`);
        }
        vs.push(`- ${label}: ${w[k]}${unit ? " " + unit : ""}`);
      }
    }
    if (vs.length) lines.push("Vital Signs:", ...vs, "");

    // Sleep & Recovery
    const sl: string[] = [];
    const sleepHours = w.sleepSecs != null
      ? `${(Number(w.sleepSecs) / 3600).toFixed(2)}`
      : w.sleepHours != null ? String(w.sleepHours) : null;
    if (sleepHours) sl.push(`  Sleep: ${sleepHours} hours`);
    if (w.sleepQuality != null) {
      const q: Record<number, string> = {1:"Great",2:"Good",3:"Average",4:"Poor"};
      sl.push(`  Sleep Quality: ${w.sleepQuality} (${q[Number(w.sleepQuality)] ?? w.sleepQuality})`);
    }
    if (w.sleepScore != null) sl.push(`  Device Sleep Score: ${w.sleepScore}/100`);
    if (w.readiness != null) sl.push(`  Readiness: ${w.readiness}/10`);
    if (sl.length) lines.push("Sleep & Recovery:", ...sl, "");

    // Menstrual
    if (w.menstrualPhase != null || w.menstrualPhasePredicted != null) {
      const ml: string[] = [];
      if (w.menstrualPhase != null) ml.push(`  Menstrual Phase: ${String(w.menstrualPhase).charAt(0).toUpperCase() + String(w.menstrualPhase).slice(1)}`);
      if (w.menstrualPhasePredicted != null) ml.push(`  Predicted Phase: ${String(w.menstrualPhasePredicted).charAt(0).toUpperCase() + String(w.menstrualPhasePredicted).slice(1)}`);
      lines.push("Menstrual Tracking:", ...ml, "");
    }

    // Subjective feelings
    const sf: string[] = [];
    for (const [k, label] of [["soreness","Soreness"],["fatigue","Fatigue"],["stress","Stress"],["mood","Mood"],["motivation","Motivation"],["injury","Injury Level"]] as [string,string][]) {
      if (w[k] != null) sf.push(`  ${label}: ${w[k]}/10`);
    }
    if (sf.length) lines.push("Subjective Feelings:", ...sf, "");

    // Nutrition
    const nf: string[] = [];
    if (w.kcalConsumed != null) nf.push(`- Calories Consumed: ${w.kcalConsumed}`);
    if (w.hydrationVolume != null) nf.push(`- Hydration Volume: ${w.hydrationVolume}`);
    if (w.hydration != null) nf.push(`  Hydration Score: ${w.hydration}/10`);
    if (nf.length) lines.push("Nutrition & Hydration:", ...nf, "");

    // Steps
    if (w.steps != null) lines.push("Activity:", `- Steps: ${w.steps}`, "");

    // Comments / lock
    if (w.comments) lines.push(`Comments: ${w.comments}`);
    if ("locked" in w) lines.push(`Status: ${w.locked ? "Locked" : "Unlocked"}`);

    return lines.join("\n");
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  npm test
  ```
  Expected: all formatting tests pass

- [ ] **Step 5: Commit**

  ```bash
  git add src/formatting.ts test/formatting.test.ts
  git commit -m "feat: formatting utilities ported from Python"
  ```

---

### Task 4: MCP entry point (stub — proves routing works)

**Files:**
- Modify: `src/index.ts`

- [ ] **Step 1: Replace generated stub with MCP skeleton**

  ```typescript
  // src/index.ts
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
  import { IntervalsClient } from "./client.js";
  import { registerActivityTools } from "./tools/activities.js";
  import { registerEventTools } from "./tools/events.js";
  import { registerWellnessTools } from "./tools/wellness.js";

  export interface Env {
    API_KEY: string;
    ATHLETE_ID: string;
  }

  export default {
    async fetch(request: Request, env: Env): Promise<Response> {
      const url = new URL(request.url);
      if (!url.pathname.startsWith("/mcp")) {
        return new Response("intervals-mcp worker", { status: 200 });
      }

      const client = new IntervalsClient(env.API_KEY, env.ATHLETE_ID);
      const server = new McpServer({ name: "intervals-mcp", version: "1.0.0" });

      // sessionIdGenerator: undefined = stateless mode (required for CF Workers)
      // Supported in @modelcontextprotocol/sdk >=1.10.0
      const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });

      registerActivityTools(server, client);
      registerEventTools(server, client);
      registerWellnessTools(server, client);

      await server.connect(transport);
      return transport.handleRequest(request);
    },
  };
  ```

- [ ] **Step 2: Create stub tool registration files so TypeScript compiles**

  Create `src/tools/activities.ts`:
  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { IntervalsClient } from "../client.js";
  export function registerActivityTools(_server: McpServer, _client: IntervalsClient): void {}
  ```

  Create `src/tools/events.ts`:
  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { IntervalsClient } from "../client.js";
  export function registerEventTools(_server: McpServer, _client: IntervalsClient): void {}
  ```

  Create `src/tools/wellness.ts`:
  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { IntervalsClient } from "../client.js";
  export function registerWellnessTools(_server: McpServer, _client: IntervalsClient): void {}
  ```

- [ ] **Step 3: Verify it compiles**

  ```bash
  npx tsc --noEmit
  ```
  Expected: no errors

- [ ] **Step 4: Smoke test locally**

  ```bash
  wrangler dev --var API_KEY:testkey --var ATHLETE_ID:i12345
  ```

  In another terminal:
  ```bash
  curl http://localhost:8787/
  ```
  Expected: `intervals-mcp worker`

  Stop wrangler with Ctrl+C.

- [ ] **Step 5: Commit**

  ```bash
  git add src/index.ts src/tools/
  git commit -m "feat: MCP entry point skeleton with stateless transport"
  ```

---

## Chunk 2: Tools — Wellness, Activities, Events

### Task 5: Wellness tool

Port from: `../intervals-mcp-server/src/intervals_mcp_server/tools/wellness.py`

**Files:**
- Modify: `src/tools/wellness.ts`

- [ ] **Step 1: Implement `registerWellnessTools`**

  Replace the stub in `src/tools/wellness.ts`:

  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { z } from "zod";
  import { IntervalsClient } from "../client.js";
  import { formatWellnessEntry } from "../formatting.js";

  function defaultDateRange(): { start: string; end: string } {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    return {
      start: start.toISOString().slice(0, 10),
      end: end.toISOString().slice(0, 10),
    };
  }

  export function registerWellnessTools(server: McpServer, client: IntervalsClient): void {
    server.tool(
      "get_wellness_data",
      "Get wellness data (HRV, resting HR, CTL, ATL, TSB, weight, sleep) for the athlete",
      {
        start_date: z.string().optional().describe("Start date YYYY-MM-DD (default: 30 days ago)"),
        end_date: z.string().optional().describe("End date YYYY-MM-DD (default: today)"),
      },
      async ({ start_date, end_date }) => {
        const { start, end } = defaultDateRange();
        const params = { oldest: start_date ?? start, newest: end_date ?? end };

        try {
          const result = await client.get<unknown[]>(
            `/athlete/${client.athleteId}/wellness`,
            params
          );
          if (!result || (Array.isArray(result) && result.length === 0)) {
            return { content: [{ type: "text", text: "No wellness data found for the specified date range." }] };
          }
          const entries = Array.isArray(result) ? result : Object.values(result as object);
          const text = "Wellness Data:\n\n" + entries
            .map(e => formatWellnessEntry(e as Record<string, unknown>))
            .join("\n\n");
          return { content: [{ type: "text", text }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching wellness data: ${e}` }] };
        }
      }
    );
  }
  ```

- [ ] **Step 2: Verify it compiles**

  ```bash
  npx tsc --noEmit
  ```

- [ ] **Step 3: Smoke test via wrangler dev**

  ```bash
  wrangler dev --var API_KEY:$INTERVALS_API_KEY --var ATHLETE_ID:$INTERVALS_ATHLETE_ID
  ```

  In another terminal, send an MCP tool call:
  ```bash
  curl -X POST http://localhost:8787/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_wellness_data","arguments":{}}}'
  ```
  Expected: JSON response with wellness text content.

- [ ] **Step 4: Commit**

  ```bash
  git add src/tools/wellness.ts
  git commit -m "feat(tools): get_wellness_data"
  ```

---

### Task 6: Activity tools

Port from: `../intervals-mcp-server/src/intervals_mcp_server/tools/activities.py`

**Files:**
- Modify: `src/tools/activities.ts`

Register all 5 activity tools (plus the `get_activity_weather` stub) in one file. Implement each following the same pattern as `get_wellness_data`.

- [ ] **Step 1: Implement `get_activities`**

  Replace the stub in `src/tools/activities.ts` with the full implementation. Start with `get_activities`:

  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { z } from "zod";
  import { IntervalsClient } from "../client.js";
  import { formatActivitySummary, formatIntervals } from "../formatting.js";

  function defaultDateRange() {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
  }

  export function registerActivityTools(server: McpServer, client: IntervalsClient): void {

    server.tool(
      "get_activities",
      "Get a list of activities for the athlete from Intervals.icu",
      {
        start_date: z.string().optional().describe("Start date YYYY-MM-DD (default: 30 days ago)"),
        end_date: z.string().optional().describe("End date YYYY-MM-DD (default: today)"),
        limit: z.number().int().optional().default(10).describe("Max activities to return"),
        include_unnamed: z.boolean().optional().default(false).describe("Include unnamed activities"),
      },
      async ({ start_date, end_date, limit, include_unnamed }) => {
        const { start, end } = defaultDateRange();
        const apiLimit = include_unnamed ? limit : limit * 3;
        const params = { oldest: start_date ?? start, newest: end_date ?? end, limit: String(apiLimit) };

        try {
          let activities = await client.get<Record<string, unknown>[]>(
            `/athlete/${client.athleteId}/activities`, params
          );
          if (!include_unnamed) {
            activities = activities.filter(a => a.name && a.name !== "Unnamed");
          }
          activities = activities.slice(0, limit);
          // Note: The Python fork retries with an older date window if filtering yields fewer
          // than `limit` results. That fallback is omitted here — over-requesting 3x compensates
          // for most cases. For sparse training windows, the result count may be < limit.
          if (!activities.length) {
            return { content: [{ type: "text", text: "No activities found in the specified date range." }] };
          }
          const text = "Activities:\n\n" + activities.map(a => formatActivitySummary(a)).join("\n\n");
          return { content: [{ type: "text", text }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching activities: ${e}` }] };
        }
      }
    );
  ```

- [ ] **Step 2: Add `get_activity_details`**

  Continue inside `registerActivityTools`:
  ```typescript
    server.tool(
      "get_activity_details",
      "Get detailed information for a specific activity",
      { activity_id: z.string().describe("The Intervals.icu activity ID") },
      async ({ activity_id }) => {
        try {
          const result = await client.get<Record<string, unknown>>(`/activity/${activity_id}`);
          const activity = Array.isArray(result) ? result[0] : result;
          return { content: [{ type: "text", text: formatActivitySummary(activity as Record<string, unknown>) }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching activity: ${e}` }] };
        }
      }
    );
  ```

- [ ] **Step 3: Add `get_activity_intervals`**

  ```typescript
    server.tool(
      "get_activity_intervals",
      "Get interval data for a specific activity",
      { activity_id: z.string().describe("The Intervals.icu activity ID") },
      async ({ activity_id }) => {
        try {
          const result = await client.get<Record<string, unknown>>(`/activity/${activity_id}/intervals`);
          if (!result || (!('icu_intervals' in result) && !('icu_groups' in result))) {
            return { content: [{ type: "text", text: "No interval data found." }] };
          }
          return { content: [{ type: "text", text: formatIntervals(result) }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching intervals: ${e}` }] };
        }
      }
    );
  ```

- [ ] **Step 4: Add `get_activity_streams`**

  Default stream types match the Python fork exactly:
  ```typescript
    server.tool(
      "get_activity_streams",
      "Get time-series stream data for a specific activity. High token cost — use only for decoupling or VI analysis.",
      {
        activity_id: z.string().describe("The Intervals.icu activity ID"),
        stream_types: z.string().optional().describe(
          "Comma-separated stream types (default: time,watts,heartrate,cadence,altitude,distance,velocity_smooth). " +
          "Available: latlng, bearing, temp, grade_smooth, w_bal, and many more — see intervals.icu docs."
        ),
      },
      async ({ activity_id, stream_types }) => {
        const types = stream_types ?? "time,watts,heartrate,cadence,altitude,distance,velocity_smooth";
        try {
          const streams = await client.get<Record<string, unknown>[]>(
            `/activity/${activity_id}/streams`, { types }
          );
          if (!streams?.length) return { content: [{ type: "text", text: "No stream data found." }] };
          let text = `Activity Streams for ${activity_id}:\n\n`;
          for (const s of streams) {
            const data = s.data as unknown[] ?? [];
            const data2 = s.data2 as unknown[] ?? [];
            const isLatlng = s.type === "latlng";
            text += `Stream: ${s.name ?? s.type} (${s.type})\n`;
            text += `  Value Type: ${s.valueType ?? "N/A"}\n`;
            text += `  Data Points: ${data.length}\n`;
            if (data.length <= 10) {
              text += `  ${isLatlng ? "Lat" : "Values"}: ${JSON.stringify(data)}\n`;
            } else {
              text += `  ${isLatlng ? "Lat" : "Values"} first 5: ${JSON.stringify(data.slice(0, 5))}\n`;
              text += `  ${isLatlng ? "Lat" : "Values"} last 5: ${JSON.stringify(data.slice(-5))}\n`;
            }
            if (data2.length) {
              if (data2.length <= 10) text += `  ${isLatlng ? "Lng" : "Data2"}: ${JSON.stringify(data2)}\n`;
              else {
                text += `  ${isLatlng ? "Lng" : "Data2"} first 5: ${JSON.stringify(data2.slice(0, 5))}\n`;
                text += `  ${isLatlng ? "Lng" : "Data2"} last 5: ${JSON.stringify(data2.slice(-5))}\n`;
              }
            }
            text += "\n";
          }
          return { content: [{ type: "text", text }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching streams: ${e}` }] };
        }
      }
    );
  ```

- [ ] **Step 5: Add `get_activity_stream_sampled`**

  Port the sampling logic from `activities.py` lines 368–433:
  ```typescript
    server.tool(
      "get_activity_stream_sampled",
      "Get sampled stream data at regular time intervals. Designed for GPS/route analysis without full token cost.",
      {
        activity_id: z.string().describe("The Intervals.icu activity ID"),
        stream_types: z.string().describe("Comma-separated stream types, e.g. 'latlng,bearing'"),
        interval_seconds: z.number().int().optional().default(1800).describe("Sample one point every N seconds (default: 1800 = 30 min)"),
      },
      async ({ activity_id, stream_types, interval_seconds }) => {
        try {
          const streams = await client.get<Record<string, unknown>[]>(
            `/activity/${activity_id}/streams`, { types: stream_types }
          );
          if (!streams?.length) return { content: [{ type: "text", text: "No stream data found." }] };

          // Find time stream for index-based sampling
          const timeStream = streams.find(s => s.type === "time");
          const timeData = (timeStream?.data as number[]) ?? [];

          let sampleIndices: number[];
          if (timeData.length) {
            sampleIndices = timeData
              .map((t, i) => ({ t, i }))
              .filter(({ t }) => t % interval_seconds === 0)
              .map(({ i }) => i);
            if (!sampleIndices.length || sampleIndices[0] !== 0) sampleIndices.unshift(0);
          } else {
            const total = Math.max(...streams.map(s => ((s.data as unknown[]) ?? []).length));
            sampleIndices = Array.from({ length: Math.ceil(total / interval_seconds) }, (_, i) => i * interval_seconds);
          }

          const output: Record<string, unknown> = {};
          for (const stream of streams) {
            if (stream.type === "time") continue;
            const data = (stream.data as unknown[]) ?? [];
            const data2 = (stream.data2 as unknown[]) ?? [];
            const sampled = sampleIndices.filter(i => i < data.length).map(i => data[i]);
            if (stream.type === "latlng") {
              const sampled2 = sampleIndices.filter(i => i < data2.length).map(i => data2[i]);
              output["latlng"] = { lats: sampled, lngs: sampled2 };
            } else if (data2.length) {
              const sampled2 = sampleIndices.filter(i => i < data2.length).map(i => data2[i]);
              output[stream.type as string] = { data: sampled, data2: sampled2 };
            } else {
              output[stream.type as string] = { data: sampled };
            }
          }
          output["interval_seconds"] = interval_seconds;
          output["total_points"] = timeData.length;
          output["sampled_points"] = sampleIndices.length;

          return { content: [{ type: "text", text: JSON.stringify(output, null, 2) }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching streams: ${e}` }] };
        }
      }
    );

    // get_activity_weather registered in Task 9 (weather chunk)

  } // end registerActivityTools
  ```

- [ ] **Step 6: Verify TypeScript compiles**

  ```bash
  npx tsc --noEmit
  ```
  Expected: no errors

- [ ] **Step 7: Commit**

  ```bash
  git add src/tools/activities.ts
  git commit -m "feat(tools): activity tools (get_activities, details, intervals, streams, sampled)"
  ```

---

### Task 7: Event tools

Port from: `../intervals-mcp-server/src/intervals_mcp_server/tools/events.py`

**Files:**
- Modify: `src/tools/events.ts`

- [ ] **Step 1: Implement all event tools**

  Replace the stub with:

  ```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { z } from "zod";
  import { IntervalsClient } from "../client.js";
  import { formatEventSummary, formatEventDetails } from "../formatting.js";

  export function registerEventTools(server: McpServer, client: IntervalsClient): void {

    server.tool(
      "get_events",
      "Get planned events/workouts for the athlete",
      {
        start_date: z.string().optional().describe("Start date YYYY-MM-DD (default: today)"),
        end_date: z.string().optional().describe("End date YYYY-MM-DD (default: 30 days from today)"),
      },
      async ({ start_date, end_date }) => {
        const today = new Date().toISOString().slice(0, 10);
        const future = new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10);
        try {
          const events = await client.get<Record<string, unknown>[]>(
            `/athlete/${client.athleteId}/events`,
            { oldest: start_date ?? today, newest: end_date ?? future }
          );
          if (!events?.length) return { content: [{ type: "text", text: "No events found." }] };
          const text = "Events:\n\n" + events.map(e => formatEventSummary(e)).join("\n\n");
          return { content: [{ type: "text", text }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching events: ${e}` }] };
        }
      }
    );

    server.tool(
      "get_event_by_id",
      "Get detailed information for a specific planned event",
      { event_id: z.string().describe("The Intervals.icu event ID") },
      async ({ event_id }) => {
        try {
          const event = await client.get<Record<string, unknown>>(
            `/athlete/${client.athleteId}/event/${event_id}`
          );
          return { content: [{ type: "text", text: formatEventDetails(event) }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error fetching event: ${e}` }] };
        }
      }
    );

    server.tool(
      "delete_event",
      "Delete a single planned event. Permanent — confirm with athlete before calling.",
      { event_id: z.string().describe("The Intervals.icu event ID to delete") },
      async ({ event_id }) => {
        try {
          await client.delete(`/athlete/${client.athleteId}/events/${event_id}`);
          return { content: [{ type: "text", text: `Event ${event_id} deleted.` }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error deleting event: ${e}` }] };
        }
      }
    );

    server.tool(
      "delete_events_by_date_range",
      "Delete all planned events in a date range. Permanent.",
      {
        start_date: z.string().describe("Start date YYYY-MM-DD"),
        end_date: z.string().describe("End date YYYY-MM-DD"),
      },
      async ({ start_date, end_date }) => {
        try {
          const events = await client.get<Record<string, unknown>[]>(
            `/athlete/${client.athleteId}/events`,
            { oldest: start_date, newest: end_date }
          );
          let deleted = 0;
          const failed: unknown[] = [];
          await Promise.all(events.map(async e => {
            try {
              await client.delete(`/athlete/${client.athleteId}/events/${e.id}`);
              deleted++; // safe: JS single-threaded event loop, no true concurrency on shared state
            } catch {
              failed.push(e.id);
            }
          }));
          return { content: [{ type: "text", text: `Deleted ${deleted} events. Failed: ${failed.length} (${failed.join(", ")})` }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Error: ${e}` }] };
        }
      }
    );

    server.tool(
      "add_or_update_event",
      "Create or update a planned workout event. See workout_doc for structured interval definitions.",
      {
        name: z.string().describe("Event name (e.g. 'Easy Run', 'Threshold Ride')"),
        workout_type: z.enum(["Ride", "Run", "Swim", "Walk", "Row"]).describe("Sport type"),
        start_date: z.string().optional().describe("Date YYYY-MM-DD (default: today)"),
        event_id: z.string().optional().describe("Provide to update an existing event"),
        moving_time: z.number().int().optional().describe("Expected duration in seconds"),
        distance: z.number().int().optional().describe("Expected distance in metres"),
        workout_doc: z.object({
          description: z.string().optional(),
          steps: z.array(z.record(z.unknown())).optional(),
        }).optional().describe(
          "Structured workout steps. Each step can have: duration (secs), distance (m), " +
          "power/hr/pace/cadence with value+units, reps with nested steps array, warmup/cooldown booleans, text label."
        ),
      },
      async ({ name, workout_type, start_date, event_id, moving_time, distance, workout_doc }) => {
        const date = start_date ?? new Date().toISOString().slice(0, 10);
        const eventData: Record<string, unknown> = {
          start_date_local: `${date}T00:00:00`,
          category: "WORKOUT",
          name,
          type: workout_type,
          moving_time,
          distance,
          // workout_doc is serialised as JSON string in description field
          // intervals.icu parses this server-side to extract workout steps
          description: workout_doc ? JSON.stringify(workout_doc) : undefined,
        };

        try {
          if (event_id) {
            const result = await client.put(
              `/athlete/${client.athleteId}/events/${event_id}`, eventData
            );
            return { content: [{ type: "text", text: `Event updated: ${JSON.stringify(result, null, 2)}` }] };
          } else {
            const result = await client.post(
              `/athlete/${client.athleteId}/events`, eventData
            );
            return { content: [{ type: "text", text: `Event created: ${JSON.stringify(result, null, 2)}` }] };
          }
        } catch (e) {
          return { content: [{ type: "text", text: `Error saving event: ${e}` }] };
        }
      }
    );

  } // end registerEventTools
  ```

- [ ] **Step 2: Verify `workout_doc` serialisation before shipping**

  The Python reference uses `str(workout_doc)` which produces Python repr, not JSON.
  `JSON.stringify` is used here instead — verify intervals.icu accepts JSON in the `description` field
  by testing with a real `add_or_update_event` call via `wrangler dev` before deploying:

  ```bash
  curl -X POST http://localhost:8787/mcp \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc":"2.0","id":1,"method":"tools/call",
      "params":{"name":"add_or_update_event","arguments":{
        "name":"Test Workout","workout_type":"Ride","start_date":"2099-12-31",
        "workout_doc":{"description":"Test","steps":[{"duration":"600","power":{"value":"60","units":"%ftp"}}]}
      }}
    }'
  ```
  Expected: success response with an event ID. If the API rejects it, check the actual format
  intervals.icu expects (may require the workout_doc stringified differently).
  Delete the test event afterwards.

- [ ] **Step 3: Verify TypeScript compiles**

  ```bash
  npx tsc --noEmit
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add src/tools/events.ts
  git commit -m "feat(tools): event tools (get, get_by_id, add_or_update, delete, delete_by_range)"
  ```

---

## Chunk 3: Weather Pipeline

### Task 8: Weather utility functions (pure — fully unit tested)

**Files:**
- Create: `src/weather.ts`
- Create: `test/weather.test.ts`

- [ ] **Step 1: Write failing tests for pure weather functions**

  Create `test/weather.test.ts`:

  ```typescript
  import { describe, it, expect } from "vitest";
  import {
    isHeadwind,
    degToCardinal,
    weathercodeToDescription,
    tempBar,
    selectOpenMeteoUrl,
  } from "../src/weather";

  describe("isHeadwind", () => {
    it("returns true when wind is directly in face (delta = 0)", () => {
      expect(isHeadwind(90, 90)).toBe(true); // travelling E, wind from E
    });

    it("returns true when delta is just under 90°", () => {
      expect(isHeadwind(0, 89)).toBe(true);
    });

    it("returns false when delta is exactly 90°", () => {
      expect(isHeadwind(0, 90)).toBe(false);
    });

    it("returns false when wind is from behind (delta = 180)", () => {
      expect(isHeadwind(90, 270)).toBe(false); // travelling E, wind from W
    });

    it("handles wrap-around correctly (positive intermediate)", () => {
      expect(isHeadwind(350, 10)).toBe(true); // (350-10+180)=520, 520%360=160, +360)%360=160, |160-180|=20 → headwind
    });

    it("handles wrap-around with negative intermediate — JS % trap", () => {
      // JS: (10-350+180)=-160, -160%360=-160 (NOT 200 like Python), fix: (-160+360)%360=200, |200-180|=20 → headwind
      expect(isHeadwind(10, 350)).toBe(true); // travelling NNE, wind from NNW — 20° delta
    });
  });

  describe("degToCardinal", () => {
    it("converts 0 to N", () => expect(degToCardinal(0)).toBe("N"));
    it("converts 90 to E", () => expect(degToCardinal(90)).toBe("E"));
    it("converts 180 to S", () => expect(degToCardinal(180)).toBe("S"));
    it("converts 270 to W", () => expect(degToCardinal(270)).toBe("W"));
    it("converts 45 to NE", () => expect(degToCardinal(45)).toBe("NE"));
  });

  describe("weathercodeToDescription", () => {
    // Implementation uses range checks (>= / <=) rather than exact-membership sets like Python.
    // This is a deliberate broadening: e.g. code 52 returns "Drizzle" here vs "Mixed conditions"
    // in Python. WMO codes 52/54/62/64/72/74 are valid so the range approach is more robust.
    it("maps 0 to Clear sky", () => expect(weathercodeToDescription(0)).toBe("Clear sky"));
    it("maps 1 to Partly cloudy", () => expect(weathercodeToDescription(1)).toBe("Partly cloudy"));
    it("maps 2 to Partly cloudy", () => expect(weathercodeToDescription(2)).toBe("Partly cloudy"));
    it("maps 3 to Overcast", () => expect(weathercodeToDescription(3)).toBe("Overcast"));
    it("maps 45 to Foggy", () => expect(weathercodeToDescription(45)).toBe("Foggy"));
    it("maps 48 to Foggy", () => expect(weathercodeToDescription(48)).toBe("Foggy"));
    it("maps 51 to Drizzle", () => expect(weathercodeToDescription(51)).toBe("Drizzle"));
    it("maps 61 to Rain", () => expect(weathercodeToDescription(61)).toBe("Rain"));
    it("maps 71 to Snow", () => expect(weathercodeToDescription(71)).toBe("Snow"));
    it("maps 80 to Rain showers", () => expect(weathercodeToDescription(80)).toBe("Rain showers"));
    it("maps 95 to Thunderstorm", () => expect(weathercodeToDescription(95)).toBe("Thunderstorm"));
    it("maps 99 to Thunderstorm", () => expect(weathercodeToDescription(99)).toBe("Thunderstorm"));
    it("maps unknown code (e.g. 100) to Mixed conditions", () => expect(weathercodeToDescription(4)).toBe("Mixed conditions"));
  });

  describe("tempBar", () => {
    it("returns two lines", () => {
      const result = tempBar(20, 18);
      expect(result.split("\n")).toHaveLength(2);
    });

    it("contains temperature values", () => {
      const result = tempBar(26.8, 31.0);
      expect(result).toContain("26.8");
      expect(result).toContain("31.0");
    });

    it("uses block characters", () => {
      const result = tempBar(30, 30);
      expect(result).toContain("█");
      expect(result).toContain("░");
    });
  });

  describe("selectOpenMeteoUrl", () => {
    it("uses forecast endpoint for recent activity (≤5 days ago)", () => {
      const recentDate = new Date(Date.now() - 2 * 864e5).toISOString().slice(0, 10);
      const url = selectOpenMeteoUrl(48.8, 2.3, recentDate);
      expect(url).toContain("api.open-meteo.com/v1/forecast");
      expect(url).toContain("past_days=");
    });

    it("uses archive endpoint for old activity (>5 days ago)", () => {
      const oldDate = "2025-01-01";
      const url = selectOpenMeteoUrl(48.8, 2.3, oldDate);
      expect(url).toContain("archive-api.open-meteo.com/v1/archive");
      expect(url).toContain("start_date=2025-01-01");
    });
  });
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  npm test
  ```
  Expected: `Cannot find module '../src/weather'`

- [ ] **Step 3: Implement pure functions in `src/weather.ts`**

  ```typescript
  // Pure utility functions — all exported for testing

  const VARIABLES = "temperature_2m,apparent_temperature,windspeed_10m,winddirection_10m,precipitation,snowfall,cloudcover,weathercode";

  export function isHeadwind(travelBearing: number, windFromDeg: number): boolean {
    // NOTE: JavaScript % returns negative for negative operands (unlike Python).
    // The `(... + 360) % 360` guard ensures a non-negative result before subtracting 180.
    const delta = Math.abs((((travelBearing - windFromDeg + 180) % 360) + 360) % 360 - 180);
    return delta < 90;
  }

  export function degToCardinal(deg: number): string {
    const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
    return dirs[Math.round(deg / 22.5) % 16];
  }

  export function weathercodeToDescription(code: number): string {
    if (code === 0) return "Clear sky";
    if (code <= 2) return "Partly cloudy";
    if (code === 3) return "Overcast";
    if (code === 45 || code === 48) return "Foggy";
    if (code >= 51 && code <= 55) return "Drizzle";
    if (code >= 61 && code <= 65) return "Rain";
    if (code >= 71 && code <= 75) return "Snow";
    if (code >= 80 && code <= 82) return "Rain showers";
    if (code >= 95) return "Thunderstorm";
    return "Mixed conditions";
  }

  export function tempBar(temp: number, feelsLike: number, width = 20): string {
    const lo = 15, hi = 45;
    const bar = (val: number) => {
      const filled = Math.max(0, Math.min(width, Math.round((val - lo) / (hi - lo) * width)));
      return "█".repeat(filled) + "░".repeat(width - filled);
    };
    return [
      `  Temp       ${temp.toFixed(1).padStart(5)}°C  ${bar(temp)}`,
      `  Feels like ${feelsLike.toFixed(1).padStart(5)}°C  ${bar(feelsLike)}`,
    ].join("\n");
  }

  export function selectOpenMeteoUrl(lat: number, lng: number, date: string): string {
    const daysAgo = Math.floor((Date.now() - new Date(date).getTime()) / 864e5);
    if (daysAgo <= 5) {
      return `https://api.open-meteo.com/v1/forecast` +
        `?latitude=${lat}&longitude=${lng}&hourly=${VARIABLES}` +
        `&past_days=${Math.min(daysAgo + 1, 5)}&forecast_days=1` +
        `&timezone=auto&wind_speed_unit=kmh`;
    }
    return `https://archive-api.open-meteo.com/v1/archive` +
      `?latitude=${lat}&longitude=${lng}&start_date=${date}&end_date=${date}` +
      `&hourly=${VARIABLES}&timezone=auto&wind_speed_unit=kmh`;
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  npm test
  ```
  Expected: all weather unit tests pass

- [ ] **Step 5: Commit**

  ```bash
  git add src/weather.ts test/weather.test.ts
  git commit -m "feat(weather): pure utility functions with full unit test coverage"
  ```

---

### Task 9: Weather pipeline + `get_activity_weather` tool

**Files:**
- Modify: `src/weather.ts` (add `computeActivityWeather`)
- Modify: `src/tools/activities.ts` (add `get_activity_weather` tool)

- [ ] **Step 1: Add `computeActivityWeather` to `src/weather.ts`**

  Append to `src/weather.ts`:

  ```typescript
  interface WaypointWeather {
    temp: number;
    feelsLike: number;
    windSpeed: number;
    windDeg: number;
    precipitation: number;
    snowfall: number;
    clouds: number;
    weathercode: number;
  }

  async function fetchWaypointWeather(
    lat: number, lng: number, date: string, hour: number
  ): Promise<WaypointWeather> {
    const url = selectOpenMeteoUrl(lat, lng, date);
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`Open-Meteo ${res.status}`);
    const data = await res.json() as { hourly: Record<string, number[]> };
    const h = data.hourly;
    const target = `${date}T${String(hour).padStart(2, "0")}:00`;
    const idx = h.time?.findIndex((t: unknown) => String(t).startsWith(target.slice(0, 13))) ?? 0;
    const i = idx >= 0 ? idx : 0;
    return {
      temp: h.temperature_2m[i],
      feelsLike: h.apparent_temperature[i],
      windSpeed: h.windspeed_10m[i],
      windDeg: h.winddirection_10m[i],
      precipitation: h.precipitation[i],
      snowfall: h.snowfall[i],
      clouds: h.cloudcover[i],
      weathercode: h.weathercode[i],
    };
  }

  export interface WeatherResult {
    description: string;
    average_temp: number;
    average_feels_like: number;
    average_wind_speed: number;
    prevailing_wind_deg: number;
    prevailing_wind_cardinal: string;
    headwind_percent: number;
    tailwind_percent: number;
    avg_yaw: number | null;
    max_rain: number;
    max_snow: number;
    average_clouds: number;
    temp_bar: string;
    source: "open-meteo";
  }

  export async function computeActivityWeather(
    date: string,
    startHour: number,
    lats: number[],
    lngs: number[],
    bearings: (number | null)[],  // full unsampled bearing array from stream
    timeElapsed: number[],        // elapsed seconds at each sampled waypoint
    sampleOriginalIndices: number[], // original stream indices of each sampled waypoint (for nearest-waypoint proximity)
  ): Promise<WeatherResult> {
    // Fetch weather for each GPS waypoint in parallel
    const weatherPoints = await Promise.all(
      lats.map((lat, i) => {
        const hour = (startHour + Math.floor((timeElapsed[i] ?? 0) / 3600)) % 24;
        return fetchWaypointWeather(lat, lngs[i], date, hour);
      })
    );

    // Aggregate
    const n = weatherPoints.length;
    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;

    const avgTemp = Math.round(avg(weatherPoints.map(w => w.temp)) * 10) / 10;
    const avgFeels = Math.round(avg(weatherPoints.map(w => w.feelsLike)) * 10) / 10;
    const avgWind = Math.round(avg(weatherPoints.map(w => w.windSpeed)) * 10) / 10;
    const avgWindDeg = Math.round(avg(weatherPoints.map(w => w.windDeg)) * 10) / 10;
    const avgClouds = Math.round(avg(weatherPoints.map(w => w.clouds)) * 10) / 10;
    const maxRain = Math.max(...weatherPoints.map(w => w.precipitation));
    const maxSnow = Math.max(...weatherPoints.map(w => w.snowfall));
    const worstCode = Math.max(...weatherPoints.map(w => w.weathercode));

    // Headwind/tailwind from bearing samples (use nearest waypoint weather).
    // `sampleOriginalIndices` holds the original stream index of each waypoint (e.g. [0, 1800, 3600, ...]).
    // We compare against bearing's array index `i` in the same original-stream-index space.
    let hwCount = 0, twCount = 0, yawSum = 0, total = 0;
    for (let i = 0; i < bearings.length; i++) {
      const b = bearings[i];
      if (b == null) continue;
      // Find nearest waypoint using original stream indices, not waypoint array positions
      const nearestWpIdx = sampleOriginalIndices.reduce((best, wpOrigIdx, wi) =>
        Math.abs(wpOrigIdx - i) < Math.abs(sampleOriginalIndices[best] - i) ? wi : best, 0
      );
      const windFrom = weatherPoints[nearestWpIdx].windDeg;
      // Use the same negative-modulo guard as isHeadwind
      const delta = Math.abs((((b - windFrom + 180) % 360) + 360) % 360 - 180);
      yawSum += delta;
      if (isHeadwind(b, windFrom)) hwCount++; else twCount++;
      total++;
    }

    return {
      description: weathercodeToDescription(worstCode),
      average_temp: avgTemp,
      average_feels_like: avgFeels,
      average_wind_speed: avgWind,
      prevailing_wind_deg: avgWindDeg,
      prevailing_wind_cardinal: degToCardinal(avgWindDeg),
      headwind_percent: total ? Math.round(hwCount / total * 1000) / 10 : 0,
      tailwind_percent: total ? Math.round(twCount / total * 1000) / 10 : 0,
      avg_yaw: total ? Math.round(yawSum / total * 10) / 10 : null,
      max_rain: maxRain,
      max_snow: maxSnow,
      average_clouds: avgClouds,
      temp_bar: tempBar(avgTemp, avgFeels),
      source: "open-meteo",
    };
  }
  ```

- [ ] **Step 2: Add `get_activity_weather` tool inside `registerActivityTools` in `src/tools/activities.ts`**

  Remove the `// get_activity_weather registered in Task 9` comment and add before the closing `}`:

  ```typescript
    server.tool(
      "get_activity_weather",
      "Get weather conditions for an outdoor activity. Fetches GPS streams + Open-Meteo data server-side. " +
      "Returns description, feels-like temp, wind speed/direction, headwind/tailwind %, precipitation flags, and ASCII temp bar.",
      { activity_id: z.string().describe("The Intervals.icu activity ID") },
      async ({ activity_id }) => {
        try {
          // Step 1: Get activity metadata for date and GPS check
          const activity = await client.get<Record<string, unknown>>(`/activity/${activity_id}`);
          const startDateLocal = activity.start_date_local as string | undefined;
          if (!startDateLocal) return { content: [{ type: "text", text: "Weather unavailable: missing start date." }] };

          const date = startDateLocal.slice(0, 10);
          const startHour = parseInt(startDateLocal.slice(11, 13), 10);

          // Step 2: Fetch GPS + bearing streams
          const streams = await client.get<Record<string, unknown>[]>(
            `/activity/${activity_id}/streams`,
            { types: "time,latlng,bearing" }
          );

          const timeStream = streams.find(s => s.type === "time");
          const latlngStream = streams.find(s => s.type === "latlng");
          const bearingStream = streams.find(s => s.type === "bearing");

          const timeData = (timeStream?.data as number[]) ?? [];
          const lats = (latlngStream?.data as number[]) ?? [];
          const lngs = (latlngStream?.data2 as number[]) ?? [];
          const bearingData = (bearingStream?.data as (number | null)[]) ?? [];

          if (!lats.length || !lngs.length) {
            return { content: [{ type: "text", text: "Weather unavailable: no GPS data for this activity." }] };
          }

          // Step 3: Sample by time stream (every 1800s).
          // NOTE: This uses the time-stream modulo approach from get_activity_stream_sampled,
          // NOT the index-stride approach in weather.py build_waypoints. The time-stream approach
          // is correct for variable-rate GPS data; the Python index-stride assumes 1 Hz GPS.
          const sampleIndices = timeData.length
            ? (() => {
                const idx = timeData.map((t, i) => ({ t, i }))
                  .filter(({ t }) => t % 1800 === 0).map(({ i }) => i);
                if (!idx.length || idx[0] !== 0) idx.unshift(0);
                return idx;
              })()
            : Array.from({ length: Math.ceil(lats.length / 1800) }, (_, i) => i * 1800);

          const sampledLats = sampleIndices.filter(i => i < lats.length).map(i => lats[i]);
          const sampledLngs = sampleIndices.filter(i => i < lngs.length).map(i => lngs[i]);
          const sampledTime = sampleIndices.filter(i => i < timeData.length).map(i => timeData[i]);

          // Step 4+5: Compute weather (parallel Open-Meteo fetches + aggregation).
          // Pass sampleIndices so computeActivityWeather can find nearest waypoint per bearing
          // sample using original stream-index proximity (not waypoint array position).
          const result = await computeActivityWeather(
            date, startHour, sampledLats, sampledLngs, bearingData, sampledTime, sampleIndices
          );

          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        } catch (e) {
          return { content: [{ type: "text", text: `Weather unavailable: ${e}` }] };
        }
      }
    );
  ```

  Also add the import at the top of `activities.ts`:
  ```typescript
  import { computeActivityWeather } from "../weather.js";
  ```

- [ ] **Step 3: Verify TypeScript compiles**

  ```bash
  npx tsc --noEmit
  ```

- [ ] **Step 4: Run all tests**

  ```bash
  npm test
  ```
  Expected: all tests pass (client + formatting + weather unit tests)

- [ ] **Step 5: Commit**

  ```bash
  git add src/weather.ts src/tools/activities.ts
  git commit -m "feat(weather): get_activity_weather tool with server-side Open-Meteo pipeline"
  ```

---

## Chunk 4: Deploy + Skill File Updates

### Task 10: Deploy to Cloudflare

> **Working directory:** Ensure you are in `intervals.icu-server/` for all steps in this task.

**Files:**
- None new — deploy existing Worker

> **Output note:** The TypeScript `WeatherResult` omits the `waypoints` array that Python's `compute_weather` returns. This is intentional — waypoints add token cost and are not used by the skill. If route-level per-waypoint data is needed in future, add it back to `WeatherResult`.

- [ ] **Step 1: Set secrets**

  ```bash
  wrangler secret put API_KEY
  # Enter your intervals.icu API key when prompted

  wrangler secret put ATHLETE_ID
  # Enter your athlete ID (e.g. i388529) when prompted
  ```

- [ ] **Step 2: Deploy**

  ```bash
  wrangler deploy
  ```
  Expected output includes the Worker URL, e.g.:
  `https://intervals-mcp.your-subdomain.workers.dev`

- [ ] **Step 3: Smoke test — MCP tool list**

  ```bash
  curl -X POST https://intervals-mcp.your-subdomain.workers.dev/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
  ```
  Expected: JSON response listing all 12 tools.

- [ ] **Step 4: Smoke test — live data call**

  ```bash
  TODAY=$(date +%Y-%m-%d)
  WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d)
  curl -X POST https://intervals-mcp.your-subdomain.workers.dev/mcp \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"get_wellness_data\",\"arguments\":{\"start_date\":\"$WEEK_AGO\",\"end_date\":\"$TODAY\"}}}"
  ```
  Expected: JSON response with real wellness data content.

- [ ] **Step 5: Connect Claude Code**

  Update `../intervals.icu-coach/.mcp.json`:
  ```json
  {
    "mcpServers": {
      "intervals-mcp": {
        "type": "http",
        "url": "https://intervals-mcp.your-subdomain.workers.dev/mcp"
      }
    }
  }
  ```

- [ ] **Step 6: Verify Claude Code sees the tools**

  In `intervals.icu-coach/`, run:
  ```bash
  claude mcp list
  ```
  Expected: `intervals-mcp` listed with HTTP transport.

- [ ] **Step 6b: Commit the `.mcp.json` update in the coach repo**

  ```bash
  # Switch to coach repo to commit the .mcp.json change
  cd ../intervals.icu-coach
  git add .mcp.json
  git commit -m "feat: switch MCP server to CF Worker HTTP transport"
  cd ../intervals.icu-server
  ```

  > **Rollback:** If smoke tests fail, revert `.mcp.json` in `intervals.icu-coach` to the previous `uvx` command before debugging the Worker.

- [ ] **Step 7: Tag and push server repo**

  ```bash
  # Ensure you are in intervals.icu-server/
  git tag v1.0.0
  git push origin main --tags
  ```

---

### Task 11: Update skill files (in `intervals.icu-coach/`)

> **Note:** These edits are in a different repo directory. Ensure you are working in `../intervals.icu-coach/` for this task.
> Read both files in full before making any edits to locate all references that need updating.

**Files:**
- Modify: `skills/triathlon-training/SKILL.md`
- Modify: `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`

- [ ] **Step 1: Read `SKILL.md` in full and locate all weather/uvx references**

  ```bash
  grep -n "weather\|uvx\|get_activity_stream_sampled\|weather.py\|stream_sampled" \
    skills/triathlon-training/SKILL.md
  ```

- [ ] **Step 2: Update MCP Tool Map in `SKILL.md`**

  Find the `## MCP Tool Map` table. Add two new rows:
  ```
  | get_activity_weather      | Get weather for an outdoor activity (GPS + Open-Meteo) | activity_id |
  | get_activity_stream_sampled | Get sampled GPS/bearing stream (used internally by get_activity_weather; callable for route analysis) | activity_id, stream_types, interval_seconds |
  ```

  Note: `get_activity_stream_sampled` does NOT currently have a row in the Tool Map — add it fresh.

- [ ] **Step 3: Update setup instructions and tool call order notes in `SKILL.md`**

  Find the Claude Code prerequisites section (likely contains `claude mcp add ... uvx ...`). Replace the `uvx`-based setup instructions with:
  ```markdown
  **Claude Code setup:** Update `.mcp.json` in this repo — `intervals-mcp` is already configured.
  Ensure the `url` points to the deployed CF Worker:
  `https://intervals-mcp.your-subdomain.workers.dev/mcp`
  ```

  Then find any tool call order notes that reference `get_activity_stream_sampled → run weather.py`. Replace with:
  ```
  get_activity_weather(activity_id)
  ```

- [ ] **Step 4: Read `DISCIPLINE_ANALYSIS.md` in full and locate all weather references**

  ```bash
  grep -n "weather\|stream_sampled\|weather.py\|Open-Meteo\|WebFetch" \
    skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  ```

- [ ] **Step 5: Update cycling `### Tools to Call` section**

  Find the cycling analysis `### Tools to Call` list (approx. lines 29–38). Replace the step referencing `get_activity_stream_sampled` + weather script with:

  > **Note:** The running section's `### Tools to Call` (approx. lines 110–119) references `get_activity_streams(stream_types="latlng,bearing")` — this is incorrect in the current file. Fix it to use `get_activity_weather` as part of Step 7.
  ```
  2. `get_activity_weather` — weather context for the session; parse returned JSON for `description`,
     `average_feels_like`, `average_wind_speed`, `prevailing_wind_cardinal`, `headwind_percent`, `tailwind_percent`
  ```

- [ ] **Step 6: Update cycling step 0 weather block**

  Find `**0. Fetch weather context**` in the cycling section. Replace the "call get_activity_stream_sampled → run weather.py" instructions with:

  ```markdown
  **0. Fetch weather context**

  Call `get_activity_weather(activity_id)`. Parse the returned JSON:
  - `description` — plain-language summary (e.g. "Partly cloudy")
  - `average_feels_like` — perceived temperature (accounts for humidity + wind)
  - `average_wind_speed`, `prevailing_wind_cardinal` — wind speed and direction
  - `headwind_percent`, `tailwind_percent` — route-aware wind impact
  - `max_rain`, `max_snow` — precipitation flags
  - `temp_bar` — ASCII temperature visualisation

  If the tool returns `"Weather unavailable: ..."` → skip weather, note unavailable, proceed to step 1.

  Lead output with: "{description} — {average_feels_like}°C feels-like, {average_wind_speed} km/h {prevailing_wind_cardinal} ({headwind_percent}% headwind / {tailwind_percent}% tailwind)"
  ```

- [ ] **Step 7: Apply same updates to running section**

  Repeat steps 5 and 6 for the running analysis section (approx. lines 110–130).

- [ ] **Step 8: Verify no remaining weather.py or stream_sampled-for-weather references**

  ```bash
  grep -n "weather.py\|Open-Meteo\|stream_sampled" \
    skills/triathlon-training/SKILL.md skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  ```
  Expected: `get_activity_stream_sampled` appears only in the MCP Tool Map (for route analysis), not in weather workflow steps.

- [ ] **Step 9: Commit**

  ```bash
  git add skills/triathlon-training/SKILL.md skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  git commit -m "feat(skill): replace weather.py with get_activity_weather MCP tool"
  ```
