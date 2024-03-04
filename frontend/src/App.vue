<script lang="ts">
import "@/assets/custom.css";
import { useUserStore } from "@/stores/user.js";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  watch: {
    $route: function () {
      this.currentLinks = this.getRouteLinks();
      if (
        !this.userStore.is_staff &&
        this.$router.currentRoute.value.path.includes("admin")
      ) {
        this.$router.push("/");
      }
    },
  },
  created() {},
  methods: {
    getRouteLinks() {
      let val = [];
      Object.keys(this.links.admin).forEach((element) => {
        if (
          this.$router.currentRoute.value.path.includes(
            this.links.admin[element].routefilter
          )
        ) {
          val = this.links.admin[element].links;
        }
      });
      return val;
    },
    async login() {
      if (this.loginMenu.loginValid) {
        const isSuccessfull = await this.userStore.signIn(
          this.loginMenu.username,
          this.loginMenu.password
        );
        if (isSuccessfull) {
          //reset logindata to prevent relogin after logout
          this.loginMenu.username = "";
          this.loginMenu.password = "";
          this.loginMenu.loginValid = false;
        }
        this.userStore.checkCredentials();
      }
    },
    async logout() {
      //reset permissions
      await this.userStore.signOut();
      this.$router.go(0);
    },
  },
  async mounted() {
    document.title = this.siteName;
    this.currentLinks = this.getRouteLinks();
  },
  data: () => {
    return {
      siteName: import.meta.env.VITE_SITENAME,
      drawer: false,
      currentLinks: [],
      loginMenu: {
        loginValid: false,
        username: "",
        password: "",
        usernameRules: [
          (v: string) => !!v || "Der Nutzername darf nicht leer sein",
          (v: string) =>
            v.length > 3 || "Der Nutzername besteht aus mindestens 3 Zeichen",
          (v: string) =>
            /^[0-9a-zA-Z]+$/.test(v) ||
            "Der Nutzername besteht nur aus Ziffern und Buchstaben",
        ],
        passwordRules: [
          (v: string) => !!v || "Das Passwortfeld darf nicht leer sein",
          (v: string) =>
            v.length > 3 || "Das Passwort besteht aus mindestens 3 Zeichen",
        ],
      },
      links: {
        admin: {
          inventory: {
            name: "Inventar",
            routefilter: "inventory",
            links: [
              { to: "/admin/inventory/rental", name: "Verleih" },
              { to: "/admin/inventory/onpremise", name: "Vorort" },
              { to: "/admin/inventory/tags", name: "Tags" },
              { to: "/admin/inventory/priorities", name: "Prioritäten" },
            ],
          },
          settings: {
            name: "Einstellungen",
            routefilter: "settings",
            links: [
              { to: "/admin/settings/texts", name: "Texte" },
              { to: "/admin/settings/users", name: "Nutzerverwaltung" },
              { to: "/admin/settings/general", name: "Einstellungen" },
            ],
          },
          rental: {
            name: "Verleih",
            routefilter: "/admin/rental",
            links: [
              {
                to: "/admin/rental/dashboard",
                name: "Geräte- und Lizenzverleih",
              },
              { to: "/admin/rental/onpremise", name: "Vorort Nutzung" },
            ],
          },
        },
      },
    };
  },
};
</script>

<template>
  <v-app :theme="userStore.theme">
    <v-navigation-drawer v-model="drawer" temporary right>
      <v-list nav dense>
        <template v-if="userStore.is_staff">
          <v-list-group no-action>
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" title="Admin"> </v-list-item>
            </template>
            <template v-for="(link, i) in links.admin" :key="i">
              <v-list-group no-active>
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props">
                    <v-list-item-title>
                      {{ link.name }}
                    </v-list-item-title>
                  </v-list-item>
                </template>
                <v-list-item
                  v-for="sublink in link.links"
                  :to="sublink.to"
                  :key="sublink.name"
                >
                  <v-list-item-title>{{ sublink.name }}</v-list-item-title>
                </v-list-item>
              </v-list-group>
            </template>
          </v-list-group>
        </template>
        <v-list-item to="/">
          <v-list-item-title> Verleih </v-list-item-title>
        </v-list-item>
        <v-list-item
          v-if="userStore.settings.onpremise_activated.value"
          to="/onpremise"
        >
          <v-list-item-title> Vorortnutzung </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar dense>
      <template v-slot:prepend>
        <v-app-bar-nav-icon
          v-if="$vuetify.display.mobile"
          @click.stop="drawer = !drawer"
        ></v-app-bar-nav-icon>
      </template>
      <v-app-bar-title @click="$router.push('/')" style="cursor: pointer">
        {{ siteName }}</v-app-bar-title
      >
      <v-tabs
        v-if="
          !$vuetify.display.mobile &&
          $router.currentRoute.value.path.includes('admin')
        "
      >
        <v-tab to="/admin/rental"> Verleih </v-tab>
        <v-tab v-if="userStore.inventory_rights" to="/admin/inventory">
          Inventar
        </v-tab>
        <v-tab v-if="userStore.inventory_rights" to="/admin/settings">
          Einstellungen
        </v-tab>
      </v-tabs>
      <!-- Main Page /Not admin Top bar-->
      <v-tabs
        v-if="
          userStore.settings.onpremise_activated.value &&
          !$vuetify.display.mobile &&
          !$router.currentRoute.value.path.includes('admin')
        "
      >
        <v-tab to="/"> Verleih </v-tab>
        <v-tab
          v-if="
            userStore.settings.onpremise_activated.value &&
            !$vuetify.display.mobile &&
            !$router.currentRoute.value.path.includes('admin')
          "
          to="/onpremise"
        >
          Vorortnutzung
        </v-tab>
      </v-tabs>
      <v-spacer v-if="!$vuetify.display.mobile"></v-spacer>
      <!-- v-tabs below the current tabs-->
      <template
        v-if="
          !$vuetify.display.mobile &&
          $router.currentRoute.value.path.includes('admin')
        "
        v-slot:extension
      >
        <v-tabs align-tabs="center" fixed-tabs>
          <!-- current links is updated on every route change, makes it easier to adjust routes. if changes are needed, adjust getRouteLinks -->
          <v-tab v-for="link in currentLinks" :key="link.to" :to="link.to">
            {{ link.name }}</v-tab
          >
        </v-tabs>
      </template>
      <template v-slot:append>
        <!-- button for the admin area, only displayed for staff-->
        <v-btn
          v-if="!$vuetify.display.mobile && userStore.is_staff"
          id="adminbutton"
          to="/admin"
        >
          Admin
        </v-btn>
        <div v-if="!$vuetify.display.mobile && userStore.is_staff">|</div>

        <!-- Account button, leads to account overview -->
        <v-btn icon>
          <v-icon icon="mdi-account"></v-icon>
          <v-menu activator="parent" :close-on-content-click="false">
            <v-card min-width="400" class="pa-3">
              <v-sheet v-if="!userStore.isLoggedIn">
                <v-form @submit.prevent="login" v-model="loginMenu.loginValid">
                  <v-text-field
                    label="Nutzername"
                    type="username"
                    v-model="loginMenu.username"
                    :rules="loginMenu.usernameRules"
                  >
                  </v-text-field>
                  <v-text-field
                    label="Passwort"
                    type="password"
                    v-model="loginMenu.password"
                    :rules="loginMenu.passwordRules"
                  >
                  </v-text-field>
                  <router-link to="/account/passwordreset">
                    Passwort vergessen?
                  </router-link>
                  <v-card-actions>
                    <v-btn type="submit" color="green" variant="flat"
                      >Login</v-btn
                    >
                    <v-spacer></v-spacer>
                    <v-btn @click="$router.push('/register')">Register</v-btn>
                  </v-card-actions>
                </v-form>
              </v-sheet>
              <v-sheet v-else>
                <v-list>
                  <v-list-item>
                    <v-btn class="w-100 justify-start" to="/account">
                      <template v-slot:prepend>
                        <v-icon icon="mdi-account"> </v-icon
                      ></template>
                      Account</v-btn
                    >
                  </v-list-item>
                  <v-list-item>
                    <v-btn class="w-100 justify-start" to="/account/processes">
                      <template v-slot:prepend>
                        <v-icon icon="mdi-animation-outline"> </v-icon
                      ></template>
                      Vorgänge</v-btn
                    >
                  </v-list-item>
                </v-list>
              </v-sheet>
              <v-card-actions v-if="userStore.isLoggedIn">
                <v-btn color="red" variant="flat" @click="logout"
                  >Ausloggen</v-btn
                >
              </v-card-actions>
            </v-card>
          </v-menu>
        </v-btn>
        <div v-if="!$vuetify.display.mobile && userStore.isLoggedIn">|</div>
        <!-- Button to switch between light and dark theme-->
        <v-btn
          :icon="
            userStore.theme == 'light'
              ? 'mdi-weather-sunny'
              : 'mdi-weather-night'
          "
          @click="
            userStore.theme = userStore.theme == 'light' ? 'dark' : 'light'
          "
        ></v-btn>
        <div v-if="userStore.isLoggedIn">|</div>
        <v-btn v-if="userStore.isLoggedIn" icon @click="$router.push('/cart')">
          <v-badge floating :content="userStore.shoppingCart.length">
            <v-icon icon="mdi-basket"></v-icon>
          </v-badge>
        </v-btn>
      </template>
    </v-app-bar>
    <v-main fluid>
      <v-alert
        class="ma-3"
        type="info"
        v-if="
          userStore.isLoggedIn &&
          'user' in userStore.user &&
          userStore.user.user.profile.automatically_verifiable &&
          !userStore.user.user.profile.verified
        "
        ><div class="text-center">
          <!-- Aktuell nur möglich wenn direkte Mitlgiedschaft zur Fakultät 7.2 besteht-->
          Die Zugehörigkeit zu einem leramtsbezogenen Studiengang kann
          möglicherweise automatisch verifiziert werden(bei direkter
          Zugehörigkeit zur Fakultät 7.2). Klicke dafür auf den folgenden Button
          und folge den Anweisungen.
        </div>
        <div class="d-flex justify-center">
          <v-btn flat variant="tonal" @click="userStore.accountVerification"
            >Verifizierung starten</v-btn
          >
        </div>
      </v-alert>
      <v-alert
        v-if="
          userStore.message.alert && !userStore.message.text.includes('html')
        "
        v-model="userStore.message['alert']"
        class="ma-3"
        :type="userStore.message['type']"
        :text="userStore.message['text']"
        closable
      />
      <div
        v-if="
          userStore.message.alert && userStore.message.text.includes('html')
        "
        v-html="userStore.message.text"
      ></div>
      <router-view />
    </v-main>
  </v-app>
</template>
<style>
.w-30 {
  width: 30% !important;
}
</style>
