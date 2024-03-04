<script setup lang="ts">
// composition api not option api
import type { RentalObjectTypeType, TagType } from "@/ts/rent.types";
import CartButton from "./CartButton.vue";
//import { useUserStore } from "@/stores/user";
defineProps<{
  thing: RentalObjectTypeType;
  tags: TagType[];
  width?: "w-100" | "w-32";
}>();
//const userStore = useUserStore();
</script>
<template>
  <v-card
    class="ma-2 pa-2"
    :class="
      width == undefined ? ($vuetify.display.mobile ? 'w-100' : 'w-32') : width
    "
    @click="$router.push('/type/' + thing['id'])"
  >
    <div class="d-flex flex-row">
      <v-avatar class="ma-3" size="90" rounded="0">
        <v-img cover aspect-ratio="1" :src="thing['image']"></v-img>
      </v-avatar>
      <v-card elevation="0" height="100" class="overflow-auto">{{
        thing.shortdescription
      }}</v-card>
    </div>
    <template v-slot:title
      ><div class="d-flex flex-wrap">
        <div class="mr-2">{{ thing["name"] }}</div>
        <v-chip v-for="tag in thing['tags']" :key="thing['id'] + tag">{{
          tags.filter((x) => x.id == tag)[0]["name"]
        }}</v-chip>
      </div>
      <hr />
    </template>
    <v-card-actions @click.stop @click="$router.push('/type/' + thing['id'])">
      <CartButton :thing="thing" />
      <!-- <v-spacer />
      <v-btn text @click.stop @click="userStore.openSuggestionsDialog(thing)"
        >Vorschläge</v-btn
      > -->
    </v-card-actions>
  </v-card>
</template>
