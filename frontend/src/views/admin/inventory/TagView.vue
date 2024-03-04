<script lang="ts">
import { useUserStore } from "@/stores/user";
export default {
  setup() {
    const userStore = useUserStore();

    return { userStore };
  },
  data: () => {
    return {
      tags: [],
      newTag: {},
    };
  },
  methods: {
    async syncTags() {
      this.tags.splice(
        0,
        this.tags.length,
        ...(await this.userStore.getFromURLWithAuth({ url: "tags" }))
      );
      console.log(this.tags);
    },
    saveTag(index: number) {
      this.userStore.patchURLWithAuth({
        url: "tags/" + this.tags[index]["id"],
        params: this.tags[index],
      });
      //setTimeout(this.syncTags, 500)
    },
    createTag() {
      this.userStore.postURLWithAuth({ url: "tags", params: this.newTag });
      setTimeout(this.syncTags, 200);
      this.newTag = {};
    },
    deleteTag(index: number) {
      this.userStore.deleteURLWithAuth({
        url: "tags/" + this.tags[index]["id"],
      });
      setTimeout(this.syncTags, 200);
    },
  },
  mounted() {
    this.syncTags();
  },
};
</script>

<template>
  <v-list>
    <div v-if="tags.length < 1">
      Keine Tags vorhanden, bitte füge welche hinzu
    </div>
    <v-list-item v-for="(tag, index) in tags" :key="tag['id']">
      <v-card class="ma-2">
        <v-text-field
          class="ma-2"
          label="Tagname"
          v-model="tag['name']"
          :readonly="!userStore.inventory_rights"
        ></v-text-field>
        <v-textarea
          class="ma-2"
          label="description"
          v-model="tag['description']"
          :readonly="!userStore.inventory_rights"
        ></v-textarea>
        <!-- TODO add color selection-->
        <v-row class="ma-2">
          <v-btn
            @click="saveTag(index)"
            v-if="userStore.inventory_rights"
            text
            flat
          >
            Speichern</v-btn
          >
          <v-btn
            @click="deleteTag(index)"
            v-if="userStore.inventory_rights"
            text
            flat
          >
            Löschen
          </v-btn>
        </v-row>
      </v-card>
    </v-list-item>
    <v-list-item v-if="userStore.inventory_rights">
      <v-text-field
        label="Tagname"
        v-model="newTag['name']"
        :readonly="!userStore.inventory_rights"
      ></v-text-field>
      <v-textarea
        label="description"
        v-model="newTag['description']"
        :readonly="!userStore.inventory_rights"
      ></v-textarea>
      <!-- TODO add color selection-->

      <v-btn @click="createTag" text flat>Erstellen</v-btn>
    </v-list-item>
  </v-list>
</template>
