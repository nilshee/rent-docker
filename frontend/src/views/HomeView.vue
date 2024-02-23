<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { RentalObjectTypeType, TagType, TextType } from "@/ts/rent.types";
import Datepicker from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
import dateFormat from "dateformat";
import SuggestionsDialog from "@/components/SuggestionsDialog.vue";
import TypeCard from "@/components/TypeCard.vue";
export default {
  components: { Datepicker, SuggestionsDialog, TypeCard },
  data: () => {
    return {
      rentableTypes: [] as RentalObjectTypeType[],
      tags: [] as TagType[],
      searchTerm: "" as string,
      neededTexts: ["frontpage"],
      texts: [] as TextType[],
      filterDialog: {
        open: false,
        selectedTags: [] as number[],
      },
    };
  },
  created() {
    this.$watch(
      "userStore.rentRange",
      async (newval) => {
        if (newval.start != null && newval.end != null) {
          // if one of both is null we do not have a range => do not curl available
          const start = dateFormat(newval.start, "yyyy-mm-dd");
          const end = dateFormat(newval.end, "yyyy-mm-dd");
          if (start > end) {
            // if start is after end null the end to prevent sideeffects (selcted could be in "forbidden" area)
            this.userStore.available = {};
            this.userStore.rentRange.end = null;
          } else {
            // both are set refresh available
            this.userStore.available = await this.userStore.getFromURLWithAuth({
              url: "rentalobjecttypes/available",
              params: {
                from_date: dateFormat(newval.start, "yyyy-mm-dd"),
                until_date: dateFormat(newval.end, "yyyy-mm-dd"),
              },
            });
          }
        }
      },
      { deep: true }
    );
  },
  setup() {
    const userStore = useUserStore();
    userStore.checkCredentials();
    return { userStore };
  },
  computed: {
    disabledLentingWeekdays() {
      let weekdays = [0, 1, 2, 3, 4, 5, 6];
      weekdays.splice(
        weekdays.indexOf(Number(this.userStore.settings.lenting_day.value) % 7),
        1
      );
      return weekdays;
    },
    disabledReturningWeekdays() {
      let weekdays = [0, 1, 2, 3, 4, 5, 6];
      weekdays.splice(
        weekdays.indexOf(
          Number(this.userStore.settings.returning_day.value) % 7
        ),
        1
      );
      return weekdays;
    },
  },
  async mounted() {
    // get the stuf around first
    this.texts = await this.userStore.getFromURLWithoutAuth({
      url: "texts",
      params: { names: this.neededTexts },
    });
    this.tags = await this.userStore.getFromURLWithoutAuth({ url: "tags" });
    this.rentableTypes.splice(
      0,
      this.rentableTypes.length,
      ...(await this.userStore.getFromURLWithoutAuth({
        url: "rentalobjecttypes",
        params: { visible: true },
      }))
    );
  },
  methods: {
    filterTypes() {
      // converts the types and corresponding tags to a Json string and filters them for the searchterm
      let filtered = this.rentableTypes;
      if (this.filterDialog.selectedTags.length > 0) {
        filtered = filtered.filter((thing) =>
          this.filterDialog.selectedTags.every((tag) =>
            thing.tags.includes(tag)
          )
        );
      }
      filtered = filtered.filter((thing) =>
        (
          JSON.stringify(thing) +
          JSON.stringify(this.tags.filter((tag) => thing.tags.includes(tag.id)))
        )
          .toLowerCase()
          .includes(this.searchTerm.toLowerCase())
      );
      return filtered;
    },
  },
};
</script>

<template>
  <!-- filterdialog-->
  <v-dialog v-model="filterDialog.open">
    <v-card>
      <v-card-title class="text-h4"
        >Filter
        <hr
      /></v-card-title>
      <v-card>
        <v-card-title> Tags </v-card-title>
        <v-card-text>
          <v-select
            :items="tags"
            v-model="filterDialog.selectedTags"
            item-title="name"
            item-value="id"
            multiple
          ></v-select
        ></v-card-text>
      </v-card>
    </v-card>
  </v-dialog>
  <!-- Rich Text from /admin/settings/texts-->
  <v-card
    v-if="
      texts.find((x) => x.name == 'frontpage') &&
      texts.find((x) => x.name == 'frontpage').content != ''
    "
    class="pa-3"
    flat
  >
    <div
      class="ql-editor ql-snow frontpage"
      v-html="texts.find((x) => x.name == 'frontpage').content"
    ></div
  ></v-card>
  <div v-else class="ma-5"></div>
  <!-- Filter-->
  <v-card flat class="d-flex justify-center px-3">
    <div :class="$vuetify.display.mobile ? 'w-100' : 'w-75'">
      <v-text-field
        v-model="searchTerm"
        prepend-icon="mdi-magnify"
        class=""
      ></v-text-field>
    </div>
    <v-btn
      icon="mdi-filter"
      flat
      @click="filterDialog.open = !filterDialog.open"
    ></v-btn>
  </v-card>
  <v-card
    v-if="userStore.isLoggedIn"
    class="d-flex flex-column align-center justify-center"
  >
    <div class="text-h5 text-center">
      Zeitraum in dem reserviert werden soll:
    </div>
    <div class="d-flex flex-wrap justify-center">
      <div class="d-flex">
        Von:<datepicker
          auto-apply
          :dark="userStore.theme == 'dark'"
          v-model="userStore.rentRange.start"
          class="mr-2"
          no-disabled-range
          :format="'dd-MM-yyyy'"
          :time-picker="false"
          :min-date="new Date(new Date().setHours(0, 0, 0, 0))"
          :disabled-week-days="disabledLentingWeekdays"
          :enable-time-picker="false"
        >
        </datepicker>
      </div>
      <div class="d-flex">
        Bis:
        <datepicker
          :auto-apply="true"
          :dark="userStore.theme == 'dark'"
          v-model="userStore.rentRange.end"
          class="mr-2"
          no-disabled-range
          :format="'dd-MM-yyyy'"
          :time-picker="false"
          :min-date="userStore.rentRange.start"
          :disabled-week-days="disabledReturningWeekdays"
          :enable-time-picker="false"
        >
        </datepicker>
      </div>
    </div>
  </v-card>
  <!-- Type enumeration-->
  <v-card class="d-flex flex-wrap justify-left" flat>
    <TypeCard
      v-for="thing in filterTypes()"
      :key="thing['id']"
      :thing="thing"
      :tags="tags"
    ></TypeCard>
  </v-card>
  <SuggestionsDialog />
</template>
