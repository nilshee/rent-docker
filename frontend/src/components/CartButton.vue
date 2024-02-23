<script setup lang="ts">
// composition api not option api
import { useUserStore } from "@/stores/user";
import type { RentalObjectTypeType } from "@/ts/rent.types";

const userStore = useUserStore();
defineProps<{
  thing: RentalObjectTypeType;
}>();
</script>

<template>
  <v-chip
    v-if="
      userStore.isLoggedIn &&
      userStore.shoppingCart.filter((x) => x['id'] == thing['id']).length > 0
    "
  >
    <template #prepend>
      <v-btn
        variant="plain"
        @click.stop
        @click="userStore.removeFromCart(thing)"
        icon="mdi-minus"
        size="small"
      ></v-btn
    ></template>
    {{ userStore.shoppingCart.filter((x) => x["id"] == thing["id"])[0].count }}
    <template #append>
      <v-btn
        variant="plain"
        @click.stop
        @click="userStore.addToCart(thing)"
        icon="mdi-plus"
        size="small"
        :disabled="
          !(thing.id in userStore.available) ||
          userStore.getNumberInCart(thing) >=
            userStore.available[thing.id].available
        "
      ></v-btn
    ></template>
  </v-chip>
  <v-btn
    v-else-if="userStore.isLoggedIn"
    variant="plain"
    @click.stop
    @click="userStore.addToCart(thing)"
    icon="mdi-basket"
    :disabled="
      !(thing.id in userStore.available) ||
      userStore.getNumberInCart(thing) >=
        userStore.available[thing.id].available
    "
  ></v-btn>
  <v-chip
    v-if="thing.id in userStore.available"
    :color="
      userStore.available[thing.id].available > 1
        ? 'green'
        : userStore.available[thing.id].available > 0
        ? 'yellow'
        : 'red'
    "
    >{{ userStore.available[thing.id].available }} verfügbar</v-chip
  >
</template>
