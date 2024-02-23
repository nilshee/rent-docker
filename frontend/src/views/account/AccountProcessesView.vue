<!-- eslint-disable vue/valid-v-slot -->
<script lang="ts">
import { useUserStore } from "@/stores/user";
import Datepicker from "@vuepic/vue-datepicker";
import dateFormat from "dateformat";
import "@vuepic/vue-datepicker/dist/main.css";
export default {
  components: { Datepicker },
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  data() {
    return {
      reservations: {
        data: [],
        headers: [
          { title: "Gegenstand", key: "objecttype.name" },
          { title: "Anzahl", key: "count" },
          { title: "reserviert von: ", key: "reserved_from" },
          { title: "reserviert bis: ", key: "reserved_until" },
          { title: "Aktionen", key: "actions", sortable: false },
        ] ,
        sortBy: [{ key: "reserved_from" }, { key: "objecttype.name" }],
        filter: {
          open: true,
          reserved_from: dateFormat(new Date(), "yyyy-mm-dd"),
          reserved_until: null,
          canceled: false,
        },
      },
      rentals: {
        data: [],
        headers: [
          { title: "Kennung", key: "rented_object.merged_identifier" },
          { title: "Gegenstand", key: "reservation.objecttype.name" },
          { title: "Ausgeliehen von:", key: "reservation.reserved_from" },
          { title: "Ausgeliehen bis:", key: "extended_until" },
          { title: "Aktionen", key: "actions", sortable: false },
        ],
        sortBy: [
          { key: "reserved_from" },
          { key: "reservation.objecttype.name" },
        ],
        filter: {
          rented_from: new Date(),
          rented_until: null,
          open: true,
        },
      },
      workplaces: [],
      bookings: {
        data: [],
        headers: [
          { title: "Tag", key: "date" },
          { title: "Von:", key: "slot_start_time" },
          { title: "Bis:", key: "slot_end_time" },
          { title: "Arbeitsplatz", key: "workplaceobj.name" },
          { title: "Aktionen", key: "actions", sortable: false },
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
    "reservations.filter.open": function () {
      this.updateData();
    },
    "reservations.filter.reserved_from": function () {
      this.updateData();
    },
    "reservations.filter.reserved_until": function () {
      this.updateData();
    },
    "reservations.filter.canceled": function () {
      this.updateData();
    },
    "rentals.filter.rented_from": function () {
      this.updateData();
    },
    "rentals.filter.rented_until": function () {
      this.updateData();
    },
    "rentals.filter.open": function () {
      this.updateData();
    },
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
      let generatedFilter = { self: true };
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
      let reservationparams = {
        self: true,
        open: this.reservations.filter.open,
        canceled: this.reservations.filter.canceled,
      };
      if (this.reservations.filter.reserved_from != null) {
        reservationparams["reserved_from"] = dateFormat(
          this.reservations.filter.reserved_from,
          "yyyy-mm-dd"
        );
      }
      if (this.reservations.filter.reserved_until != null) {
        reservationparams["reserved_until"] = dateFormat(
          this.reservations.filter.reserved_until,
          "yyyy-mm-dd"
        );
      }
      // fetch rentals
      let rentalparams = { self: true, open: this.rentals.filter.open };
      if (this.rentals.filter.rented_from != null) {
        rentalparams["from"] = dateFormat(
          this.rentals.filter.rented_from,
          "yyyy-mm-dd"
        );
      }
      if (this.rentals.filter.rented_until != null) {
        rentalparams["until"] = dateFormat(
          this.rentals.filter.rented_until,
          "yyyy-mm-dd"
        );
      }
      this.userStore
        .getFromURLWithAuth({
          url: "reservations",
          params: reservationparams,
        })
        .then((response) => {
          this.reservations.data = response;
        });

      this.userStore
        .getFromURLWithAuth({
          url: "rentals",
          params: rentalparams,
        })
        .then((response) => {
          this.rentals.data = response;
        });
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
    cancelReservation(item) {
      this.userStore
        .postURLWithAuth({ url: "reservations/" + item.id + "/cancel" })
        .then(() => this.updateData());
    },
    extendRentalPeriod(item) {
      this.userStore
        .postURLWithAuth({ url: "rentals/" + item.id + "/extend" })
        .then(() => this.updateData());
    },
    getDisabledExtensionButtonState(item): boolean {
      let until_date = new Date(Date.parse(item.reserved_until));
      // only allow extentsions of rentals if they are less than 3 days in the future
      return (
        !item.extendable ||
        Math.floor(
          (until_date.getTime() - new Date().getTime()) / (24 * 3600 * 1000)
        ) > 2
      );
    },
  },
  computed: {},
};
</script>

<template>
  <v-card class="ma-2">
    <v-card class="mb-2">
      <v-data-table
        :items="reservations.data"
        :headers="reservations.headers"
        :sortBy="reservations.sortBy"
      >
        <template v-slot:top>
          <v-toolbar flat>
            <v-toolbar-title>Meine Reservierungen</v-toolbar-title>

            <template #append>
              <v-menu location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn icon v-bind="props">
                    <v-icon>mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>

                <v-list density="compact">
                  <v-list-item>
                    Von:
                    <datepicker
                      auto-apply
                      :dark="userStore.theme == 'dark'"
                      v-model="reservations.filter.reserved_from"
                      :format="'dd-MM-yyyy'"
                      :time-picker="false"
                    >
                    </datepicker>
                  </v-list-item>
                  <v-list-item>
                    Bis:
                    <datepicker
                      auto-apply
                      :dark="userStore.theme == 'dark'"
                      v-model="reservations.filter.reserved_until"
                      :format="'dd-MM-yyyy'"
                      :time-picker="false"
                    >
                    </datepicker>
                  </v-list-item>
                  <v-list-item>
                    <v-checkbox-btn
                      label="Nur offene Vorgänge anzeigen"
                      v-model="reservations.filter.open"
                    />
                  </v-list-item>
                  <v-list-item>
                    <v-checkbox-btn
                      label="Zeige stornierte Vorgänge"
                      v-model="reservations.filter.canceled"
                    />
                  </v-list-item>
                </v-list> </v-menu
            ></template> </v-toolbar
        ></template>
        <template #no-data>Aktuell keine Reservierungen</template>
        <!-- Design Name Column-->
        <template v-slot:item.objecttype.name="{ item }">
          <v-chip v-if="item.raw.canceled != null" color="red">{{
            item.raw.objecttype.name
          }}</v-chip>
          <v-chip v-else-if="item.raw.fullfilled" color="green">{{
            item.raw.objecttype.name
          }}</v-chip>
          <span v-else>{{ item.raw.objecttype.name }}</span></template
        >
        <!-- actions slot -->
        <template v-slot:item.actions="{ item }">
          <v-tooltip
            location="start"
            :text="
              item.raw.canceled == null && !item.raw.fullfilled
                ? 'stornieren'
                : 'bereits storniert/nicht stornierbar'
            "
          >
            <template v-slot:activator="{ props }">
              <span v-bind="props">
                <v-btn
                  icon="mdi-cancel"
                  color="red"
                  variant="plain"
                  @click="cancelReservation(item.raw)"
                  :disabled="item.raw.canceled != null || item.raw.fullfilled"
                ></v-btn>
              </span>
            </template>
          </v-tooltip>
        </template>
        <!-- Footer with legend-->
        <template #footer.prepend
          >Legende:<v-chip color="red">storniert</v-chip
          ><v-chip color="green">abgeholt</v-chip
          ><v-spacer></v-spacer></template
      ></v-data-table>
    </v-card>
    <!-- Rental operations datatable-->
    <v-card class="mb-2">
      <v-data-table :items="rentals.data" :headers="rentals.headers">
        <!-- Top Toolbar-->
        <template v-slot:top>
          <v-toolbar flat>
            <v-toolbar-title>Mein laufende Ausleihvorgänge</v-toolbar-title>
            <!-- append filter menu to toolbar-->
            <template #append
              ><v-menu location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn icon v-bind="props">
                    <v-icon>mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>
                <v-list>
                  <v-list-item>
                    Von:
                    <datepicker
                      auto-apply
                      :dark="userStore.theme == 'dark'"
                      v-model="rentals.filter.rented_from"
                      :format="'dd-MM-yyyy'"
                      :time-picker="false"
                    >
                    </datepicker>
                  </v-list-item>
                  <v-list-item>
                    Bis:
                    <datepicker
                      auto-apply
                      :dark="userStore.theme == 'dark'"
                      v-model="rentals.filter.rented_until"
                      :format="'dd-MM-yyyy'"
                      :time-picker="false"
                    >
                    </datepicker>
                  </v-list-item>
                  <v-list-item>
                    <v-checkbox
                      label="Nur Unzurückgegebene zeigen"
                      v-model="rentals.filter.open"
                    />
                  </v-list-item>
                </v-list> </v-menu
            ></template> </v-toolbar
        ></template>
        <!-- identifier slot design-->
        <template v-slot:item.rented_object.merged_identifier="{ item }">
          <v-chip
            color="green"
            v-if="item.raw.received_back_at != null"
            :text="item.raw.rented_object.merged_identifier"
          >
          </v-chip>
          <v-chip
            color=""
            v-else-if="
              item.raw.reveived_back_at == null &&
              new Date(Date.parse(item.raw.reserved_until)) < new Date()
            "
          ></v-chip>
          <span v-else>{{
            item.raw.rented_object.merged_identifier
          }}</span></template
        >
        <template #no-data>Aktuell keine Gegenstände ausgeliehen</template>
        <!-- actions slot -->
        <template v-slot:item.actions="{ item }">
          <!-- extend button-->
          <v-tooltip
            location="start"
            :text="
              getDisabledExtensionButtonState(item.raw)
                ? 'Verlängerung nicht möglich'
                : 'Um eine Woche verlängern'
            "
          >
            <template v-slot:activator="{ props }">
              <!-- span to prevent props from disabling the tooltip on disabled button-->
              <span v-bind="props">
                <v-btn
                  icon="mdi-clock-plus-outline"
                  variant="plain"
                  @click="extendRentalPeriod(item.raw)"
                  :disabled="getDisabledExtensionButtonState(item.raw)"
                ></v-btn>
              </span>
            </template>
          </v-tooltip>
        </template>
        <!-- prepend a legend to footer -->
        <template #footer.prepend
          >Legende:<v-chip color="red">überfällig!!</v-chip
          ><v-chip color="green">zurückerhalten</v-chip><v-spacer></v-spacer
        ></template>
      </v-data-table>
    </v-card>
    <v-card v-if="userStore.settings.onpremise_activated">
      <v-data-table
        :items="bookings.data"
        :headers="bookings.headers"
        :sortBy="bookings.sortBy"
      >
        <template v-slot:item.date="{ item }">
          <v-chip
            v-if="item.raw.canceled != null"
            color="red"
            :text="item.raw.date"
          />
          <v-sheet v-else>{{ item.raw.date }}</v-sheet>
        </template>
        <!-- Toolbar on top of data-table -->
        <template v-slot:top>
          <v-toolbar flat>
            <v-toolbar-title>Vorort-Reservierungen</v-toolbar-title><v-spacer />
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
              </v-list>
            </v-menu>
          </v-toolbar>
        </template>
        <!-- Aktionen -->
        <template v-slot:item.actions="{ item }">
          <v-btn
            color="red"
            variant="plain"
            :disabled="item.raw.canceled != null"
            icon="mdi-cancel"
            @click="
              userStore.postURLWithAuth({
                url: 'onpremisebooking/' + item.raw.id + '/cancel',
              });
              updateData();
            "
          ></v-btn>
        </template>
        <!-- Footer with legends-->
        <template #footer.prepend
          >Legende:<v-chip color="red">storniert</v-chip><v-spacer></v-spacer
        ></template>
      </v-data-table>
    </v-card>
  </v-card>
</template>
