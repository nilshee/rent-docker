<!-- eslint-disable vue/valid-v-slot -->
<script lang="ts">
import { useUserStore } from "@/stores/user";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  data() {
    return {
      users: [],
      headers: [
        { title: "Vorname", key: "first_name" },
        { title: "Nachname", key: "last_name" },
        { title: "Nutzername", key: "username" },
        { title: "Email", key: "email" },
        { title: "Alle Rechte", key: "is_superuser" },
        { title: "Verleihrechte", key: "has_lending_rights" },
        { title: "Adminlogin", key: "is_staff" },
        { title: "Login aktiviert", key: "is_active" },
        { title: "Prioritätenklasse", key: "profiledata.prio.id" },
      ],
      priorities: [],
    };
  },
  mounted() {
    this.userStore.getFromURLWithAuth({ url: "users" }).then((data) => {
      this.users = data;
      console.log(data);
    });
    this.userStore.getFromURLWithAuth({ url: "priority" }).then((data) => {
      console.log(data);
      this.priorities = data;
    });
  },
};
</script>

<template>
  <v-card>
    <v-data-table :headers="headers" :items="users">
      <template v-slot:item.is_superuser="{ item }">
        <v-checkbox-btn
          v-model="item.raw.is_superuser"
          @click="
            userStore.patchURLWithAuth({
              url: 'users/' + item.raw.id,
              params: { is_superuser: !item.raw.is_superuser },
            })
          "
        ></v-checkbox-btn>
      </template>
      <template v-slot:item.is_active="{ item }">
        <v-checkbox-btn
          v-model="item.raw.is_active"
          @click="
            userStore.patchURLWithAuth({
              url: 'users/' + item.raw.id,
              params: { is_active: !item.raw.is_active },
            })
          "
        ></v-checkbox-btn>
      </template>
      <template v-slot:item.is_staff="{ item }">
        <v-checkbox-btn
          v-model="item.raw.is_staff"
          @click="
            userStore.patchURLWithAuth({
              url: 'users/' + item.raw.id,
              params: { is_staff: !item.raw.is_staff },
            })
          "
        ></v-checkbox-btn>
      </template>
      <template v-slot:item.profiledata.prio.id="{ item }">
        <v-select
          class="ma-auto"
          variant="solo"
          :items="priorities"
          item-value="id"
          item-title="name"
          v-model="item.raw.profiledata.prio.id"
          @update:model-value="
            userStore.patchURLWithAuth({
              url: 'users/' + item.raw.profiledata.id,
              params: { profile: item.raw.profiledata.prio.id },
            })
          "
        >
        </v-select>
      </template>
      <template v-slot:item.has_lending_rights="{ item }">
        <v-checkbox-btn
          v-model="item.raw.has_lending_rights"
          @click="
            userStore.postURLWithAuth({
              url: 'users/' + item.raw.id + '/toggle_permission',
              params: { permission: 'lending_access' },
            })
          "
        ></v-checkbox-btn>
      </template>
    </v-data-table>
  </v-card>
</template>
