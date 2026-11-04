export type UserRole = "owner" | "admin" | "student";
export type ContentType = "text" | "video";
export type ThemePreference = "light" | "dark" | "system";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  theme: ThemePreference;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface SiteInfo {
  site_name: string;
  logo_url: string | null;
  accent_color: string | null;
  hero_badge: string | null;
  hero_title: string;
  hero_text: string | null;
  currency: string;
  demo_payments: boolean;
}

export type SiteSettingsPayload = Partial<
  Pick<SiteInfo, "site_name" | "logo_url" | "accent_color" | "hero_badge" | "hero_title" | "hero_text">
>;

export interface Course {
  id: number;
  title: string;
  slug: string;
  price: string | null;
  description: string;
  cover_image_url: string | null;
  owner_id: number;
}

export interface CourseCard extends Course {
  module_count: number;
  lesson_count: number;
  free_lesson_count: number;
  total_minutes: number;
  question_count: number;
}

export interface Module {
  id: number;
  course_id: number;
  title: string;
  position: number;
  price: string | null;
}

export interface LessonSummary {
  id: number;
  module_id: number;
  title: string;
  content_type: ContentType;
  position: number;
  is_free_preview: boolean;
  duration_minutes: number | null;
}

export interface LessonOutline extends LessonSummary {
  is_open: boolean;
  question_count: number;
}

export interface Lesson extends LessonSummary {
  content: string;
}

export interface ModuleOutline {
  id: number;
  title: string;
  position: number;
  price: string | null;
  is_purchased: boolean;
  lessons: LessonOutline[];
}

export interface CourseOutline extends Course {
  is_purchased: boolean;
  modules: ModuleOutline[];
}

export type PurchaseTarget = { course_id: number } | { module_id: number };

export interface Purchase {
  id: number;
  user_id: number;
  user_email: string;
  course_id: number | null;
  module_id: number | null;
  course_title: string;
  course_slug: string;
  module_title: string | null;
  purchased_at: string;
  payment_reference: string;
}

export interface LessonProgress {
  lesson_id: number;
  completed_at: string | null;
  completed: boolean;
}

export interface CourseProgress {
  course_id: number;
  total_lessons: number;
  completed_lessons: number;
  percent: number;
  lessons: LessonProgress[];
}

export interface MyCourse {
  course_id: number;
  title: string;
  slug: string;
  has_purchase: boolean;
  total_lessons: number;
  completed_lessons: number;
  percent: number;
}

export interface CoursePayload {
  title: string;
  slug: string;
  price: string | null;
  description: string;
  cover_image_url: string | null;
}

export type LegalSlug = "privacy" | "consent";

export interface LegalPage {
  slug: LegalSlug;
  title: string;
  content: string;
  updated_at: string | null;
  is_template: boolean;
}

export type QuestionKind ="single" | "multiple" | "text";

export interface AnswerResult {
  question_id: number;
  is_correct: boolean;
  option_ids: number[];
  text: string | null;
  correct_option_ids: number[];
  accepted_answers: string[];
  explanation: string;
  answered_at: string;
}

export interface QuestionPublic {
  id: number;
  position: number;
  kind: QuestionKind;
  prompt: string;
  options: { id: number; text: string }[];
  result: AnswerResult | null;
}

export interface QuestionAdmin {
  id: number;
  lesson_id: number;
  position: number;
  kind: QuestionKind;
  prompt: string;
  explanation: string;
  options: { id: number; text: string; is_correct: boolean }[];
}

export interface QuestionPayload {
  kind: QuestionKind;
  prompt: string;
  explanation: string;
  options: { text: string; is_correct: boolean }[];
}

export interface ModulePayload {
  title: string;
  price: string | null;
}

export interface LessonPayload {
  title: string;
  content_type: ContentType;
  content: string;
  is_free_preview: boolean;
  duration_minutes: number | null;
  module_id: number;
}
