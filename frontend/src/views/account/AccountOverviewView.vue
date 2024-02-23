<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { UserType } from "@/ts/rent.types";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  async created() {},
  data() {
    return {
      user: {} as UserType,
      newsletter: false,
    };
  },
  mounted() {
    this.userStore
      .getFromURLWithAuth({ url: "users/" + this.userStore.user.user.id })
      .then((rsp) => {
        this.user = { ...rsp };
      });
  },
  watch: {},
  methods: {},
};
</script>
<template>
  <v-card class="ma-3">
    <v-sheet>
      <v-alert type="warning">
        Aktuell ist die Bearbeitung deiner Daten nicht über diese Seite möglich.
      </v-alert>
    </v-sheet>
    <v-sheet>
      <v-text-field :readonly="true" label="Nutzername" v-model="user.username">
      </v-text-field>
      <v-text-field :readonly="true" label="Email" v-model="user.email">
      </v-text-field>
      <v-text-field :readonly="true" label="Vorname" v-model="user.first_name">
      </v-text-field>
      <v-text-field :readonly="true" label="Nachname" v-model="user.last_name">
      </v-text-field>
      <v-checkbox label="Newsletter" v-model="newsletter" :readonly="true">
      </v-checkbox>
      <v-sheet
        v-if="
          userStore.user.user.profile.automatically_verifiable &&
          !userStore.user.user.profile.verified
        "
      >
        Dein Account ist nicht automatisch verifizierbar. Bitte bringe eine
        Bluecard und eine Studienbescheinigung zu deiner nächsten Ausleihe mit.
      </v-sheet>
    </v-sheet>
  </v-card>
</template>
