<script lang="ts">
import { useUserStore } from "@/stores/user";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  data() {
    return {
      settings: [] as { id: number; type: string; value: string }[],
    };
  },
  async mounted() {
    this.settings = (
      await this.userStore.getFromURLWithAuth({
        url: "settings",
      })
    ).sort((a, b) => {
      const result = a.type.charCodeAt(0) - b.type.charCodeAt(0);
      return result;
    });
  },
  methods: {
    async uploadDocxTemplate() {
      const data = await this.userStore.getFromURLWithAuth({
        url: "files",
        params: { name: "rental_form" },
      });
      let formData = new FormData();
      console.log(this.$refs.rental_form);
      formData.append("file", this.$refs["rental_form"]["files"][0]);
      const resp = await this.userStore.patchURLWithAuth({
        url: "files/" + data[0]["id"],
        params: formData,
      });
      if (!String(resp.status).startsWith("2")) {
        this.userStore.alert("upload Fehlgeschlagen", "error");
      }
    },
  },
};
</script>
<template>
  <v-card class="pa-5 ma-2">
    <v-row>
      <v-col>
        <div class="text-h4 mb-5">Ausleihformularvorlage</div>
        <v-file-input
          ref="rental_form"
          accept="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ></v-file-input>
        <div class="d-flex">
          <v-btn
            class="ma-2"
            @click="
              userStore.downloadFileWithAuth({
                url: 'files/download',
                params: { name: 'rental_form' },
              })
            "
            >Download Template</v-btn
          >
          <v-btn class="ma-2" @click="uploadDocxTemplate">Upload</v-btn>
        </div>
      </v-col>
      <v-col>
        <v-list>
          <v-list-item-title
            >Die folgenden Placeholder können verwendet
            werden:</v-list-item-title
          >
          <v-list-item
            ><a target="_blank" href="https://docxtpl.readthedocs.io/en/latest/"
              >Hier sind die Docs für mehr info</a
            ></v-list-item
          >
          <v-list-item><pre>reserver.last_name</pre></v-list-item>
          <v-list-item><pre>reserver.first_name</pre></v-list-item>
          <v-list-item><pre>reserver.email</pre></v-list-item>
          <v-list-item>
            <pre>rented_items</pre>
            als Array mit den folgenden attributen:
            <v-list>
              <v-list-item><pre>count</pre></v-list-item>
              <v-list-item><pre>identifier</pre></v-list-item>
              <v-list-item><pre>reserved_from</pre></v-list-item>
              <v-list-item><pre>reserved_until</pre></v-list-item>
            </v-list>
          </v-list-item>
        </v-list>
      </v-col>
    </v-row>
  </v-card>
  <v-card class="pa-5 ma-2">
    <div class="text-h4">Settings</div>
    <div class="ml-2">
      (Aktuell ohne Validation. Also bitte aufpassen :) Tage sind 1-7 Mon-Son)
    </div>
    <v-list>
      <v-list-item v-for="setting in settings" :key="setting.id">
        <v-list-item-title>{{ setting.type }}</v-list-item-title>
        <v-list-item>
          <div class="d-flex">
            <v-text-field v-model="setting.value"></v-text-field
            ><v-btn
              @click="
                userStore.patchURLWithAuth({
                  url: 'settings/' + setting.id,
                  params: { value: setting.value },
                })
              "
            >
              Update</v-btn
            >
          </div></v-list-item
        >
      </v-list-item>
    </v-list>
  </v-card>
</template>
