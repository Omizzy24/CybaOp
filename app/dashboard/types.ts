export interface TrackMetric {
  track_id: string;
  title: string;
  engagement_rate: number;
  performance_score: number;
  plays_percentile: number;
  is_outlier: boolean;
  outlier_direction: string;
}

export interface Metrics {
  total_plays: number;
  total_likes: number;
  total_comments: number;
  total_reposts: number;
  avg_engagement_rate: number;
  catalog_concentration: number;
  all_track_metrics: TrackMetric[];
}

export interface Trends {
  best_release_day: string | null;
  best_release_hour: number | null;
  strongest_era_description: string;
  confidence: number;
  growth_velocity_7d?: number;
  growth_velocity_30d?: number;
  growth_velocity_90d?: number;
  growth_accelerating?: boolean;
  anomaly_tracks?: string[];
}

export interface Era {
  era_id: string;
  start: string;
  end: string;
  track_count: number;
  total_plays: number;
  avg_engagement_rate: number;
  top_track: string;
  genres: string[];
  avg_duration_ms: number;
}

export interface EraFingerprint {
  avg_duration_ms: number;
  dominant_genre: string;
  genre_distribution: Record<string, number>;
  avg_plays: number;
  avg_engagement: number;
  track_count: number;
}

export interface Insight {
  category: string;
  headline: string;
  detail: string;
  confidence: number;
  actionable: boolean;
  recommendation: string;
}

export interface Report {
  user_id: string;
  track_count: number;
  top_tracks: TrackMetric[];
  metrics?: Metrics | null;
  trends?: Trends | null;
  insights: Insight[];
  eras?: Era[];
  era_fingerprint?: EraFingerprint | null;
  tier: string;
  processing_time_ms: number;
  nodes_executed: string[];
}

export interface AnalyticsData {
  success: boolean;
  message?: string;
  report?: Report | null;
  processing_time_ms?: number;
}

export interface HistoryPoint {
  day: string;
  total_plays: number;
  total_likes: number;
  track_count: number;
}

// --- Workflow Types ---

export type WorkflowStatus = "active" | "paused" | "completed" | "failed";
export type StepStatus = "pending" | "active" | "completed" | "failed" | "skipped";
export type RemediationOutcomeType = "resolved" | "partially_resolved" | "unresolved";

export interface WorkflowStep {
  step_name: string;
  label: string;
  status: StepStatus;
  output: Record<string, unknown> | null;
  skippable: boolean;
  started_at: string | null;
  completed_at: string | null;
}

export interface WorkflowSession {
  id: string;
  workflow_type: string;
  status: WorkflowStatus;
  current_step: string | null;
  steps: WorkflowStep[];
  context: Record<string, unknown>;
  health_score: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface WorkflowListData {
  sessions: WorkflowSession[];
  total: number;
}

export interface HealthScorePoint {
  score: number;
  components: Record<string, number | null>;
  computed_at: string;
  explanation: string | null;
}

export interface HealthScoreHistory {
  history: HealthScorePoint[];
  current_score: number | null;
}
