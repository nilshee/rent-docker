<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { WorkplaceType } from "@/ts/rent.types";
import Datepicker from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
import dateFormat from "dateformat";
export default {
  components: { Datepicker },
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  async created() {},
  data() {
    return {
      workplaces: [] as WorkplaceType[],
      bookings: {
        data: [],
        headers: [
          { title: "Tag", key: "date" },
          { title: "Von:", key: "slot_start_time" },
          { title: "Bis:", key: "slot_end_time" },
          { title: "Name:", key: "userobj.first_name" },
          { title: "Nachname:", key: "userobj.last_name" },
          { title: "Arbeitsplatz", key: "workplaceobj.name" },
          { title: "Aufgetaucht", key: "showed_up" },
        ],
        sortBy: [{ key: "date" }, { key: "slot_start_time" }],
        changeable: false,
        filter: {
          from_date: new Date(),
          until_date: null,
          canceled: false,
        },
      },
    };
  },
  mounted() {
    this.updateData();
  },
  watch: {
    "bookings.filter.from_date": function () {
      this.updateData();
    },
    "bookings.filter.until_date": function () {
      this.updateData();
    },
    "bookings.filter.canceled": function () {
      this.updateData();
    },
  },
  methods: {
    updateData() {
      let generatedFilter = {};
      if (this.bookings.filter.from_date != null) {
        generatedFilter["from_date"] = dateFormat(
          this.bookings.filter.from_date,
          "isoDate"
        );
      }
      if (this.bookings.filter.until_date != null) {
        generatedFilter["until_date"] = dateFormat(
          this.bookings.filter.until_date,
          "isoDate"
        );
      }
      if (this.bookings.filter.canceled != null) {
        generatedFilter["canceled"] = this.bookings.filter.canceled;
      }
      this.userStore
        .getFromURLWithAuth({ url: "workplace" })
        .then((fetchedworkplaces) => {
          this.workplaces = fetchedworkplaces;
          this.userStore
            .getFromURLWithAuth({
              url: "onpremisebooking",
              params: generatedFilter,
            })
            .then((data) => {
              data = data.map((booking) => {
                return {
                  // add more information
                  date: dateFormat(booking.slot_start, "isoDate"),
                  slot_start_time: dateFormat(booking.slot_start, "HH:MM"),
                  slot_end_time: dateFormat(booking.slot_end, "HH:MM"),
                  workplaceobj: this.workplaces.find(
                    (x) => booking.workplace == x.id
                  ),
                  ...booking,
                };
              });
              this.bookings.data = data;
              console.log(this.bookings.data);
            });
        });
    },
  },
};
</script>

<template>
  <v-card class="ma-2 pa-3">
    <v-data-table
      :items="bookings.data"
      :headers="bookings.headers"
      :sortBy="bookings.sortBy"
    >
      <template v-slot:item.showed_up="{ item }">
        <v-checkbox
          v-model="item.raw.showed_up"
          @click="
            userStore.patchURLWithAuth({
              url: 'onpremisebooking/' + item.raw.id,
              params: { showed_up: !item.raw.showed_up },
            })
          "
          :disabled="
            (item.raw.showed_up && !bookings.changeable) ||
            item.raw.canceled != null
          "
        />
      </template>
      <template v-slot:item.date="{ item }">
        <v-chip
          v-if="item.raw.canceled != null"
          color="red"
          :text="item.raw.date"
        />
        <v-sheet v-else>{{ item.raw.date }}</v-sheet>
      </template>
      <template v-slot:top>
        <v-toolbar flat>
          <v-toolbar-title>Vorgänge</v-toolbar-title><v-spacer />
          <v-menu location="bottom">
            <template v-slot:activator="{ props }">
              <v-btn icon v-bind="props">
                <v-icon>mdi-dots-vertical</v-icon>
              </v-btn>
            </template>

            <v-list>
              <v-list-subheader> Filter </v-list-subheader>
              <v-list-item
                ><v-sheet class="d-flex align-center">
                  <v-sheet class="mr-auto"> Von:</v-sheet>

                  <datepicker
                    auto-apply
                    :dark="userStore.theme == 'dark'"
                    v-model="bookings.filter.from_date"
                    :format="'dd-MM-yyyy'"
                    :time-picker="false"
                  >
                  </datepicker>
                </v-sheet>
              </v-list-item>
              <v-list-item
                ><v-sheet class="d-flex align-center">
                  <v-sheet class="mr-auto"> Bis:</v-sheet>
                  <datepicker
                    auto-apply
                    :dark="userStore.theme == 'dark'"
                    v-model="bookings.filter.until_date"
                    :format="'dd-MM-yyyy'"
                    :time-picker="false"
                  >
                  </datepicker
                ></v-sheet>
              </v-list-item>
              <v-list-item>
                <v-checkbox-btn
                  label="Auch stornierte anzeigen"
                  v-model="bookings.filter.canceled"
                />
              </v-list-item>
              <v-list-subheader> Einstellungen </v-list-subheader>
              <v-list-item>
                <v-checkbox-btn
                  label="Aufgetaucht änderbar"
                  v-model="bookings.changeable"
                />
              </v-list-item>
            </v-list>
          </v-menu>
        </v-toolbar>
      </template>
      <!-- Footer with legends-->
      <template #footer.prepend
        >Legende:<v-chip color="red">storniert</v-chip><v-spacer></v-spacer
      ></template>
    </v-data-table>
  </v-card>
</template>
