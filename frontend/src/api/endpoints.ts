import { request } from "./client";
import type {
  AnswerResult,
  ContentType,
  Course,
  CourseCard,
  CourseOutline,
  CoursePayload,
  CourseProgress,
  LegalPage,
  LegalSlug,
  Lesson,
  LessonPayload,
  LessonProgress,
  LessonSummary,
  Module,
  ModulePayload,
  MyCourse,
  Purchase,
  PurchaseTarget,
  QuestionAdmin,
  QuestionPayload,
  QuestionPublic,
  SiteInfo,
  SiteSettingsPayload,
  ThemePreference,
  Token,
  User,
  UserRole,
} from "./types";

export const api = {
  site: () => request<SiteInfo>("GET", "/site"),
  updateSite: (data: SiteSettingsPayload) => request<SiteInfo>("PATCH", "/site", data),

  auth: {
    register: (email: string, password: string, consent: boolean) =>
      request<User>("POST", "/auth/register", { email, password, personal_data_consent: consent }),
    requestPasswordReset: (email: string) =>
      request<{ detail: string }>("POST", "/auth/password-reset/request", { email }),
    confirmPasswordReset: (token: string, password: string) =>
      request<void>("POST", "/auth/password-reset/confirm", { token, password }),
    login: (email: string, password: string) =>
      request<Token>("POST", "/auth/login", new URLSearchParams({ username: email, password })),
    me: () => request<User>("GET", "/auth/me"),
    updateMe: (data: { theme: ThemePreference }) => request<User>("PATCH", "/auth/me", data),
  },

  courses: {
    list: () => request<CourseCard[]>("GET", "/courses"),
    bySlug: (slug: string) =>
      request<CourseOutline>("GET", `/courses/by-slug/${encodeURIComponent(slug)}`),
    get: (id: number) => request<CourseOutline>("GET", `/courses/${id}`),
    create: (data: CoursePayload) => request<Course>("POST", "/courses", data),
    update: (id: number, data: Partial<CoursePayload>) =>
      request<Course>("PATCH", `/courses/${id}`, data),
    remove: (id: number) => request<void>("DELETE", `/courses/${id}`),
    createModule: (courseId: number, data: ModulePayload) =>
      request<Module>("POST", `/courses/${courseId}/modules`, data),
    reorderModules: (courseId: number, ids: number[]) =>
      request<Module[]>("PUT", `/courses/${courseId}/modules/order`, { ids }),
    progress: (courseId: number) =>
      request<CourseProgress>("GET", `/courses/${courseId}/progress`),
  },

  modules: {
    update: (id: number, data: Partial<ModulePayload>) =>
      request<Module>("PATCH", `/modules/${id}`, data),
    remove: (id: number) => request<void>("DELETE", `/modules/${id}`),
    createLesson: (
      moduleId: number,
      data: { title: string; content_type: ContentType; duration_minutes?: number | null },
    ) =>
      request<Lesson>("POST", `/modules/${moduleId}/lessons`, data),
    reorderLessons: (moduleId: number, ids: number[]) =>
      request<LessonSummary[]>("PUT", `/modules/${moduleId}/lessons/order`, { ids }),
  },

  lessons: {
    get: (id: number) => request<Lesson>("GET", `/lessons/${id}`),
    update: (id: number, data: Partial<LessonPayload>) =>
      request<Lesson>("PATCH", `/lessons/${id}`, data),
    remove: (id: number) => request<void>("DELETE", `/lessons/${id}`),
    start: (id: number) => request<LessonProgress>("POST", `/lessons/${id}/progress/start`),
    setCompleted: (id: number, completed: boolean) =>
      request<LessonProgress>("PUT", `/lessons/${id}/progress`, { completed }),
  },

  purchases: {
    checkout: (target: PurchaseTarget) => request<Purchase>("POST", "/purchases/checkout", target),
    mine: () => request<Purchase[]>("GET", "/purchases/me"),
    list: () => request<Purchase[]>("GET", "/purchases?limit=200"),
    grant: (data: PurchaseTarget & { user_email: string; payment_reference?: string }) =>
      request<Purchase>("POST", "/purchases", data),
    revoke: (id: number) => request<void>("DELETE", `/purchases/${id}`),
  },

  progress: {
    mine: () => request<MyCourse[]>("GET", "/progress/me"),
  },

  legal: {
    list: () => request<LegalPage[]>("GET", "/legal"),
    get: (slug: LegalSlug) => request<LegalPage>("GET", `/legal/${slug}`),
    update: (slug: LegalSlug, data: { title: string; content: string }) =>
      request<LegalPage>("PUT", `/legal/${slug}`, data),
  },

  quiz: {
    forLesson: (lessonId: number) =>
      request<QuestionPublic[]>("GET", `/lessons/${lessonId}/questions`),
    answer: (questionId: number, data: { option_ids?: number[]; text?: string }) =>
      request<AnswerResult>("POST", `/questions/${questionId}/answer`, data),
    manage: (lessonId: number) =>
      request<QuestionAdmin[]>("GET", `/lessons/${lessonId}/questions/manage`),
    create: (lessonId: number, data: QuestionPayload) =>
      request<QuestionAdmin>("POST", `/lessons/${lessonId}/questions`, data),
    replace: (questionId: number, data: QuestionPayload) =>
      request<QuestionAdmin>("PUT", `/questions/${questionId}`, data),
    remove: (questionId: number) => request<void>("DELETE", `/questions/${questionId}`),
    reorder: (lessonId: number, ids: number[]) =>
      request<QuestionAdmin[]>("PUT", `/lessons/${lessonId}/questions/order`, { ids }),
  },

  users: {
    list: (query: string) =>
      request<User[]>("GET", `/users?limit=200&q=${encodeURIComponent(query)}`),
    setRole: (id: number, role: UserRole) => request<User>("PATCH", `/users/${id}/role`, { role }),
  },
};
