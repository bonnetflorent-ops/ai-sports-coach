export interface User {
  id: string;
  email: string;
  first_name: string;
  sports: string[];
  level: 'débutant' | 'intermédiaire' | 'avancé';
  goals: Record<string, unknown>;
  health_data: Record<string, unknown>;
  equipment: string[];
  weekly_slots: WeeklySlot[];
  onboarding_completed: boolean;
  badge_count: number;
  created_at: string;
}

export interface WeeklySlot {
  day: string;
  time: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  user_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens_used: number;
  created_at: string;
}

export interface MetricValue {
  name: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
}

export interface DashboardData {
  metrics: MetricValue[];
  chart: ChartPoint[];
  upcoming_session: UpcomingSession | null;
  goal_progress: GoalProgress | null;
}

export interface ChartPoint {
  date: string;
  ctl: number;
  atl: number;
  tsb: number;
}

export interface UpcomingSession {
  date: string;
  type: string;
  duration: string;
  description: string;
}

export interface GoalProgress {
  name: string;
  target: string;
  current: string;
  percent: number;
}

export interface AthleteModel {
  physique: Record<string, unknown>;
  etat_actuel: Record<string, unknown>;
  blessures: Record<string, unknown>[];
  patterns: Record<string, unknown>[];
  preferences: Record<string, unknown>;
  objectifs: Record<string, unknown>;
  contradictions: Record<string, unknown>[];
  meta: Record<string, unknown>;
}

export interface Feedback {
  message_id: string;
  type: 'like' | 'dislike';
  detail?: string;
}

export interface OnboardingPhase1 {
  sport: string;
  level: string;
  goal: string;
  injuries: string;
  equipment: string;
  slots: string;
}

export interface OnboardingPhase2 {
  weight?: number;
  height?: number;
  age?: number;
  gender?: string;
  email?: string;
}

export interface ParQAnswer {
  question: string;
  answer: boolean;
}
