<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { VueElement } from "vue";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  created() {
    // do not allow person here if they are already logged in
    this.userStore.checkCredentials().then((isLoggedIn) => {
      if (isLoggedIn) {
        this.$router.push("/");
      }
    });
  },
  data() {
    return {
      registrationForm: {
        valid: false,
        data: {
          last_name: "",
          first_name: "",
          username: "",
          password: "",
          confirmPassword: "",
          email: "",
          profile: {
            newsletter: false,
          },
        },
        notEmptyRules: [
          (v: string) => !!v || "Das Passwort darf nicht leer sein.",
        ],
        passwordRules: [
          (v: string) => !!v || "Das Passwort darf nicht leer sein.",
          (v: string) =>
            v.length > 7 || "Das Passwort muss mindestens 8 Zeichen enthalten.",
        ] as ((v: string) => boolean | string)[],
        usernameRules: [
          (v: string) => !!v || "Der Nutzername darf nicht leer sein",
          (v: string) =>
            v.length > 3 || "Der Nutzername besteht aus mehr als 3 Zeichen",
          (v: string) =>
            /^[0-9a-z]+$/.test(v) ||
            "Der Nutzername besteht nur aus Ziffern und Buchstaben",
        ],
        emailRules: [
          // (v: string) =>
          //   new RegExp(
          //     useUserStore().settings.email_validation_regex.value,
          //     "i"
          //   ).test(v) || "Die Email ist nicht vom Format @...rwth-aachen.de",
        ] as ((v: string) => boolean | string)[],
      },
    };
  },
  methods: {
    revalidateForm() {
      // we need to tell typescript that validate exists
      const form = this.$refs.registrationForm as VueElement & {
        validate(): () => boolean;
      };
      form.validate();
    },
    async register() {
      if (this.registrationForm.valid) {
        let msg = "";
        let type = "success" as "warning" | "success" | "error" | "info";
        const ret = await this.userStore.postURLWithoutAuth({
          url: "users",
          params: this.registrationForm.data,
        });
        if (String(ret.status).startsWith("2")) {
          msg =
            "Dein Account wurde angelegt, bitte klicke auf den Link in der Email.";
          this.userStore.alert(msg, type, 10000);
          this.$router.push("/");
        }
      }
    },
  },
  mounted() {
    this.registrationForm.passwordRules.splice(
      0,
      0,
      () =>
        this.registrationForm.data.password ==
          this.registrationForm.data.confirmPassword ||
        "Das Passwort stimmt nicht mit der Wiederholung überein"
    );
    // we do it here to not use useUserStore
    this.registrationForm.emailRules.splice(
      0,
      0,
      (v: string) =>
        new RegExp(
          this.userStore.settings.email_validation_regex.value,
          "i"
        ).test(v) ||
        "Die Email ist nicht vom Format " +
          this.userStore.settings.email_validation_regex.value
    );
  },
  computed: {},
};
</script>
<template>
  <v-card class="ma-3">
    <v-container class="">
      <div class="text-h3">Registrierung</div>
      <hr class="my-2" />
      <v-form
        @submit.prevent="register"
        v-model="registrationForm.valid"
        ref="registrationForm"
      >
        <v-text-field
          :rules="registrationForm.notEmptyRules"
          type="lastname"
          label="Nachname"
          v-model="registrationForm.data.last_name"
          required
        />
        <v-text-field
          :rules="registrationForm.notEmptyRules"
          type="firstname"
          label="Vorname"
          v-model="registrationForm.data.first_name"
          required
        />
        <v-text-field
          :rules="registrationForm.usernameRules"
          type="username"
          label="Nutzername"
          v-model="registrationForm.data.username"
          required
        />
        <v-text-field
          type="email"
          label="Email"
          :rules="registrationForm.emailRules"
          v-model="registrationForm.data.email"
          required
        />
        <v-text-field
          type="password"
          label="Passwort"
          :rules="registrationForm.passwordRules"
          v-model="registrationForm.data.password"
          @input="revalidateForm()"
          required
        />
        <v-text-field
          type="password"
          label="Passwortwiederholung"
          :rules="registrationForm.passwordRules"
          v-model="registrationForm.data.confirmPassword"
          @input="revalidateForm()"
          required
        />
        <v-checkbox
          type="checkbox"
          label="Newsletteranmeldung"
          v-model="registrationForm.data.profile.newsletter"
          @input="revalidateForm()"
          required
        />
        <v-btn type="submit">Registrieren</v-btn>
      </v-form>
    </v-container>
  </v-card>
</template>
