<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { VueElement } from "vue";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  async created() {},
  data() {
    return {
      username: "",
      email: "",
      password: "",
      passwordRepeat: "",
      passwordResetFormValid: false,
      passwordRules: [
        (v: string) => !!v || "Das Passwort darf nicht leer sein.",
        (v: string) =>
          v.length > 7 || "Das Passwort muss mindestens 8 Zeichen enthalten.",
      ] as ((v: string) => boolean | string)[],
    };
  },
  async mounted() {
    this.passwordRules.splice(
      0,
      0,
      () =>
        this.password == this.passwordRepeat ||
        "Das Passwort stimmt nicht mit der Wiederholung überein"
    );
    await this.$router.isReady();
  },
  watch: {},
  methods: {
    async resetPassword() {
      this.userStore.postURLWithoutAuth({
        url: "users/passwordreset",
        params: { username: this.username, email: this.email },
      });
      this.userStore.alert(
        "Falls ein Account zu diesen Daten existiert bekommst du eine Email mit einem Link zum zurücksetzen deines Passworts",
        "info"
      );
      this.$router.push("/");
    },
    async confirmPasswordReset() {
      if (this.passwordResetFormValid) {
        console.log("commiting new password");
        this.userStore
          .postURLWithoutAuth({
            url: "users/passwordreset_confirm",
            params: { hash: this.$route.query.hash, password: this.password },
          })
          .then((rsp) => {
            if (rsp.status.toString().startsWith("2")) {
              this.userStore.alert("Passwort erfolgreich geändert", "success");
              this.$router.push("/");
            }
          });
      } else {
        this.revalidateForm();
      }
    },
    revalidateForm() {
      // we need to tell typescript that validate exists
      const form = this.$refs.passwordreset as VueElement & {
        validate(): () => boolean;
      };
      form.validate();
    },
  },
};
</script>
<template>
  <v-card class="ma-3 pa-2">
    <v-sheet v-if="!('hash' in $route.query)">
      <v-form @submit.prevent="resetPassword">
        <v-text-field v-model="username" label="Nutzername"> </v-text-field>
        <v-text-field v-model="email" label="Email"> </v-text-field>
        <v-btn type="submit"> Passwort zurücksetzen </v-btn>
      </v-form>
    </v-sheet>
    <v-sheet v-else>
      <v-form
        @submit.prevent="confirmPasswordReset"
        v-model="passwordResetFormValid"
        ref="passwordreset"
      >
        <v-text-field
          v-model="password"
          label="Passwort"
          :rules="passwordRules"
          type="password"
          @input="revalidateForm()"
        ></v-text-field>
        <v-text-field
          v-model="passwordRepeat"
          :rules="passwordRules"
          label="Passwortwiederholung"
          type="password"
          @input="revalidateForm()"
        ></v-text-field>
        <v-btn type="submit">Neues Passwort setzen</v-btn>
      </v-form>
    </v-sheet>
  </v-card>
</template>
