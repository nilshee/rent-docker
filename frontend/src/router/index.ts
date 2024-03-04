import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/account/processes",
      name: "AccountProcesses",
      component: () => import("@/views/account/AccountProcessesView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/account/passwordreset/:hash?",
      name: "AccountPasswordReset",
      component: () => import("@/views/account/AccountPasswordResetView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/account",
      name: "Account",
      component: () => import("@/views/account/AccountOverviewView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/type/:id",
      component: () => import("@/views/TypeView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/register",
      name: "registerView",
      component: () => import("@/views/account/RegisterView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/onpremise",
      name: "onpremiseView",
      component: () => import("@/views/OnPremiseBookingView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/onpremise/:id",
      name: "onpremise",
      component: () => import("@/views/OnPremiseBookingView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/cart",
      name: "cartView",
      component: () => import("@/views/CartView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/validate/:hash",
      name: "EmailValidationView",
      component: () => import("@/views/EmailValidationView.vue"),
      meta: { requiresAdmin: false },
    },
    {
      path: "/admin/rental/dashboard",
      name: "rentalDashboard",
      component: () => import("@/views/admin/rental/RentalDashboardView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/rental/onpremise",
      name: "onpremiseDashboard",
      component: () => import("@/views/admin/rental/OnPremiseView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/inventory/rental",
      name: "rentalinventoryview",
      component: () =>
        import("@/views/admin/inventory/RentalInventoryView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/inventory/tags",
      name: "tagsView",
      component: () => import("@/views/admin/inventory/TagView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/inventory/onpremise",
      name: "onPremiseInventoryView",
      component: () =>
        import("@/views/admin/inventory/OnPremiseInventoryView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/inventory/priorities",
      name: "priorityManagement",
      component: () =>
        import("@/views/admin/inventory/PriorityManagementView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/settings/users",
      name: "userManagement",
      component: () => import("@/views/admin/settings/UserManagementView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/settings/texts",
      name: "textManagement",
      component: () => import("@/views/admin/settings/TextManagementView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/settings/general",
      name: "generalSettings",
      component: () => import("@/views/admin/settings/GeneralSettingsView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      // redirect rental button to a default case in this case the rental dashboard
      path: "/admin",
      redirect: () => {
        return { path: "/admin/rental/dashboard" };
      },
    },
    {
      // redirect rental button to a default case in this case the rental dashboard
      path: "/admin/rental",
      redirect: () => {
        return { path: "/admin/rental/dashboard" };
      },
    },
    {
      // default case
      path: "/admin/settings",
      redirect: () => {
        return { path: "/admin/settings/texts" };
      },
    },
    {
      //default case
      path: "/admin/inventory",
      redirect: () => {
        return { path: "/admin/inventory/rental" };
      },
    },
    {
      path: "/:catchAll(.*)",
      component: () => import("@/views/errorpages/404CatchAll.vue"),
    },
  ],
});

router.beforeEach(async (to) => {
  // only allow access to areas that people are supposed
  const userStore = useUserStore();
  await userStore.refreshSettings();
  if (to.meta.requiresAdmin) {
    // hits performance but only the admin site
    await userStore.checkCredentials();
    if (!userStore.is_staff) {
      return { path: "/" };
    }
  } else {
    userStore.checkCredentials();
  }
});

export default router;
