<script setup lang="ts">
// composition api not option api
import { useUserStore } from "@/stores/user";
import { reactive } from "vue";
import type { RentalObjectTypeType, TagType } from "@/ts/rent.types";
import TypeCard from "./TypeCard.vue";

const userStore = useUserStore();
let rentableTypes = reactive([] as RentalObjectTypeType[]);
let tags = reactive([] as TagType[]);

userStore
  .getFromURLWithoutAuth({
    url: "rentalobjecttypes",
    params: { visible: true },
  })
  .then((data) => (rentableTypes = data));
userStore.getFromURLWithoutAuth({ url: "tags" }).then((data) => (tags = data));
</script>

<script lang="ts">
export default {
  components: {
    TypeCard,
  },
};
</script>

<template>
  <!-- displayed if something is added to cart and this dialog is currently not open-->
  <v-dialog v-model="userStore.suggestions.dialogOpen">
    <v-card class="text-center mx-auto" scrollbar>
      <v-sheet class="pa-2 text-h6 text-center">
        Hier sind ein paar zu deiner Auswahl passende Gegenstände:
      </v-sheet>
      <v-list>
        <v-list-item
          v-for="thing in rentableTypes.filter((x) =>
            userStore.suggestions.data.map((x) => x.suggestion).includes(x.id)
          )"
          :key="thing['id']"
        >
          <template v-slot:title>
            <v-sheet
              class="overflow-auto text-wrap"
              flat
              v-if="
                userStore.suggestions.data.find((x) => x.suggestion == thing.id)
                  .description != ''
              "
            >
              <v-sheet
                >Grund für den Vorschlag von <em>{{ thing.name }}</em
                >:<br
              /></v-sheet>
              {{
                userStore.suggestions.data.find((x) => x.suggestion == thing.id)
                  .description
              }}</v-sheet
            >
          </template>
          <TypeCard :thing="thing" :tags="tags" width="w-100"></TypeCard>
        </v-list-item>
      </v-list>
      <v-card-actions
        ><v-spacer /><v-btn @click="userStore.suggestions.dialogOpen = false"
          >Schließen</v-btn
        ></v-card-actions
      >
    </v-card>
  </v-dialog>
</template>
