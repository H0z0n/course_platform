import { createBrowserRouter, RouterProvider } from "react-router";
import { AuthProvider } from "./auth/AuthContext";
import { RequireAuth, RequireStaff } from "./auth/guards";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { CatalogPage } from "./pages/CatalogPage";
import { CoursePage } from "./pages/CoursePage";
import { LessonPage } from "./pages/LessonPage";
import { MyLearningPage } from "./pages/MyLearningPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { SiteProvider } from "./site/SiteContext";
import { ThemeProvider } from "./theme/ThemeContext";

const router = createBrowserRouter([
  {
    element: <Layout />,
    hydrateFallbackElement: <Spinner />,
    children: [
      { index: true, element: <CatalogPage /> },
      { path: "courses/:slug", element: <CoursePage /> },
      { path: "courses/:slug/lessons/:lessonId", element: <LessonPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        path: "my",
        element: (
          <RequireAuth>
            <MyLearningPage />
          </RequireAuth>
        ),
      },
      {
        path: "admin",
        element: (
          <RequireStaff>
            <AdminLayout />
          </RequireStaff>
        ),
        children: [
          {
            index: true,
            lazy: async () => ({
              Component: (await import("./pages/admin/AdminCoursesPage")).AdminCoursesPage,
            }),
          },
          {
            path: "courses/new",
            lazy: async () => ({
              Component: (await import("./pages/admin/AdminCoursesPage")).NewCoursePage,
            }),
          },
          {
            path: "courses/:courseId",
            lazy: async () => ({
              Component: (await import("./pages/admin/CourseEditorPage")).CourseEditorPage,
            }),
          },
          {
            path: "courses/:courseId/lessons/:lessonId",
            lazy: async () => ({
              Component: (await import("./pages/admin/LessonEditorPage")).LessonEditorPage,
            }),
          },
          {
            path: "purchases",
            lazy: async () => ({
              Component: (await import("./pages/admin/PurchasesPage")).PurchasesPage,
            }),
          },
          {
            path: "users",
            lazy: async () => ({
              Component: (await import("./pages/admin/UsersPage")).UsersPage,
            }),
          },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

export function App() {
  return (
    <SiteProvider>
      <AuthProvider>
        <ThemeProvider>
          <RouterProvider router={router} />
        </ThemeProvider>
      </AuthProvider>
    </SiteProvider>
  );
}
