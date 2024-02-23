<script lang="ts">
import type { ReservationType } from "@/ts/rent.types";
import { useUserStore } from "@/stores/user";
import Datepicker from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
import dateFormat from "dateformat";
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
        //the grouping keys are generated in updateData
        groupBy: [{ key: "grouping1" }, { key: "grouping2" }],
        sortBy: [{ key: "reserved_from" }],
        filter: {
          open: true,
          reserved_from: null,
          reserved_until: null,
          canceled: false,
        },
        headers: [
          { title: "Actions", key: "actions", sortable: false },
          { title: "Gegenstand", key: "objecttype.name" },
          { title: "Anzahl", key: "count" },
          { title: "reserviert von", key: "reserved_from" },
          { title: "reserviert bis", key: "reserved_until" },
        ],
        open: true,
      },
      rentals: {
        data: [],
        filter: { open: true, rented_from: new Date(), rented_until: null },
        groupBy: [{ key: "grouping1" }, { key: "grouping2" }],
        sortBy: [{ key: "extended_until" }],
        headers: [
          { title: "Actions", key: "actions", sortable: false },
          { title: "Rückgabedatum", key: "extended_until" },
          { title: "Gegenstand", key: "reservation.objecttype.name" },
          { title: "Identifier", key: "merged_identifier" },
          { title: "zurückerhalten", key: "received_back_at" },
          // { title: "Vorname", key: "reservation.reserver.user.first_name" },
          // { title: "Nachname", key: "reservation.reserver.user.last_name" },
        ],
        rentalsDialog: {
          open: false,
          selectedAsReturned: [],
          // relatedItem is the item which has been selected in the table and from which properties we will fetch the rest
          relatedItem: null,
        },
      },
      handleDialog: {
        valid_selection: false,
        open: false,
        possiblePriorities: [],
        selectedPriority: null,
        reservations: [] as ReservationType[],
      },
    };
  },
  mounted() {
    this.updateData();
  },
  watch: {
    // update data if one of our filter changes
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
    "handleDialog.reservations": {
      handler() {
        var localreservations = this.handleDialog.reservations.filter((x) => {
          if ("selectedObjects" in x) {
            return x.count != x.selectedObjects.length;
          }
        });
        this.handleDialog.valid_selection = localreservations.length == 0;
      },
      deep: true,
    },
  },
  methods: {
    getDate(date) {
      return dateFormat(date, "yyyy-mm-dd HH:ss");
    },
    commitPriority(userProfile) {
      this.userStore.patchURLWithAuth({
        url: "profile/" + userProfile.id,
        params: { prio_id: this.handleDialog.selectedPriority, verified: true },
      });
      window.history.go();
    },
    async updateData() {
      let reservationparams = {
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
      let rentalparams = { open: this.rentals.filter.open };
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
      let reservationData = await this.userStore.getFromURLWithAuth({
        url: "reservations",
        params: reservationparams,
      });
      this.reservations.data = reservationData.map((x) => {
        return {
          ...x,
          grouping1: "Abholdatum: " + x.reserved_from,
          grouping2:
            x.reserver.user.first_name + " " + x.reserver.user.last_name,
        };
      });
      let data = [];

      this.userStore
        .getFromURLWithAuth({
          url: "rentals",
          params: rentalparams,
        })
        .then((response) => {
          // reorder and prepare data
          response.map((x) => {
            // console.log(x);
            data.push({
              ...x,
              //create human readable identifier
              merged_identifier:
                x.reservation.objecttype.prefix_identifier +
                x.rented_object.internal_identifier,
              grouping1: "Rückgabedatum: " + x.extended_until,
              grouping2:
                x.reservation.reserver.user.first_name +
                " " +
                x.reservation.reserver.user.last_name,
            });
            //console.log(data);
          });
          this.rentals.data = data;
        });
      //console.log(this.rentals.data);
    },
    async openHandleDialog(item) {
      console.log(this.reservations.data);
      this.handleDialog.reservations = await this.reservations.data.filter(
        (x) =>
          x.reserver.id == item.reserver.id &&
          x.reserved_from == item.reserved_from &&
          x.canceled == null
      );
      console.log(this.handleDialog.reservations);
      var tempselectedObjects = [];
      await this.handleDialog.reservations.forEach(
        async (selectedReservation) => {
          tempselectedObjects = (
            await this.userStore.getFromURLWithAuth({
              url:
                "reservations/" + selectedReservation.id + "/selectedobjects",
            })
          ).map((x) => {
            // merge the identifiers for better recognition
            return {
              ...x,
              merged_identifier:
                selectedReservation.objecttype.prefix_identifier +
                String(x.internal_identifier),
            };
          });
          selectedReservation["selectableObjects"] = (
            await this.userStore.getFromURLWithAuth({
              url:
                "rentalobjecttypes/" +
                selectedReservation.objecttype.id +
                "/freeobjects",
            })
          ).map((x) => {
            // merge the identifiers for better recognition
            return {
              ...x,
              merged_identifier:
                selectedReservation.objecttype.prefix_identifier +
                String(x.internal_identifier),
            };
          });
          selectedReservation["selectableObjects"] =
            selectedReservation["selectableObjects"].concat(
              tempselectedObjects
            );
          //selected objects are only ids
          selectedReservation["selectedObjects"] = tempselectedObjects.map(x => x['id']);
        }
      );

      if (!item.reserver.verified) {
        this.handleDialog.possiblePriorities =
          await this.userStore.getFromURLWithAuth({ url: "priority" });
      }
      this.handleDialog.open = true;
    },
    openRentalDialog(item) {
      this.rentals.rentalsDialog.open = true;
      this.rentals.rentalsDialog.relatedItem = item;
    },
    returnSelectedItems() {
      this.userStore
        .postURLWithAuth({
          url: "rentals/return",
          params: this.rentals.rentalsDialog.selectedAsReturned,
        })
        .then(() =>
          this.updateData().then(() => {
            this.rentals.rentalsDialog.open = false;
            this.rentals.rentalsDialog.selectedAsReturned = [];
          })
        );
    },
    turnReservationsIntoRentals() {
      this.userStore
        .postURLWithAuth({
          url: "rentals/bulk",
          params: this.handleDialog.reservations,
        })
        .then(() => {});
    },
    handOutReservations() {
      //save currently selected objects
      this.turnReservationsIntoRentals();
      var reservationids = this.handleDialog.reservations.map(x => x.id)
      this.userStore
        .postURLWithAuth({
          url: "rentals/bulkhandout",
          params: {reservations: reservationids},
        })
        .then(() => {});
    },
    downloadForm() {
      this.userStore.downloadFilledInTemplateWithAuth({
        url: "reservations/download_form",
        params: this.handleDialog.reservations,
      });
    },
  },
};
</script>

<template>
  <v-card>
    <v-data-table
      class="pa-4"
      :headers="reservations.headers"
      :items="reservations.data"
      :group-by="reservations.groupBy"
      :sort-by="reservations.sortBy"
    >
      <template v-slot:top>
        <v-toolbar flat>
          <v-toolbar-title>Reservierungen</v-toolbar-title>

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
          ></template>
        </v-toolbar>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn
          size="small"
          class="mr-2"
          flat
          @click="openHandleDialog(item.raw)"
          icon="mdi-pencil"
          :disabled="item.raw.canceled != null"
        ></v-btn>
        <v-btn
          @click="
            userStore.postURLWithAuth({
              url: 'reservations/' + item.raw.id + '/cancel',
            });
            updateData();
          "
          icon="mdi-cancel"
          variant="plain"
          color="red"
        ></v-btn>
      </template>
      <template v-slot:no-data>
        <div class="text-center">Keine Reservierungen</div>
      </template>
    </v-data-table>
    <v-data-table
      class="pa-4"
      :headers="rentals.headers"
      :items="rentals.data"
      :group-by="rentals.groupBy"
      :sort-by="rentals.sortBy"
    >
      <template v-slot:item.actions="{ item }">
        <v-icon
          v-if="item.raw.received_back_at == null"
          size="small"
          class="mr-2"
          @click="openRentalDialog(item.raw)"
        >
          mdi-pencil
        </v-icon>
        <v-icon
          v-if="item.raw.extendable"
          size="small"
          @click="
            userStore.postURLWithAuth({
              url: 'rentals/' + item.raw.id + '/extend',
            });
            updateData();
          "
        >
          mdi-clock
        </v-icon>
      </template>
      <template v-slot:item.received_back_at="{ item }">
        {{
          item.raw.received_back_at != null
            ? getDate(new Date(Date.parse(item.raw.received_back_at)))
            : ""
        }}
      </template>
      <template v-slot:top>
        <v-toolbar flat>
          <v-toolbar-title>Laufende Verleihvorgänge</v-toolbar-title
          ><v-spacer />
          <v-menu location="bottom">
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
            </v-list>
          </v-menu>
        </v-toolbar>
      </template>
      <template v-slot:no-data>
        <div class="text-center">Keine laufenden Verleihvorgänge</div>
      </template>
    </v-data-table>
  </v-card>
  <v-dialog v-model="handleDialog.open">
    <v-card class="pa-3">
      <div class="text-h4">Verleih</div>
      <v-sheet
        class="my-3"
        v-if="!handleDialog.reservations[0].reserver.verified"
      >
        Bitte einmal bitte die Berechtigung des Nutzers überprüfen und die
        passende Klasse wählen:<br />
        <v-select
          :items="handleDialog.possiblePriorities"
          item-value="id"
          item-title="name"
          v-model="handleDialog.selectedPriority"
          label="Priorität"
        />
        <v-btn @click="commitPriority(handleDialog.reservations[0].reserver)"
          >bestätigen</v-btn
        >
      </v-sheet>
      <v-card
        class="pa-3"
        min-height="290px"
        v-for="reservation in handleDialog.reservations"
        :key="reservation.id"
      >
        <v-row>
          <v-col>
            <v-list>
              <v-list-item-title> Daten</v-list-item-title>
              <v-list-item>
                <v-list-item-subtitle>Name:</v-list-item-subtitle>
                {{
                  reservation.reserver.user.first_name +
                  " " +
                  reservation.reserver.user.last_name
                }}
              </v-list-item>
              <v-list-item>
                <v-list-item-subtitle>Verliehen von:</v-list-item-subtitle>
                {{ reservation.reserved_from }}
              </v-list-item>
              <v-list-item>
                <v-list-item-subtitle>Verliehen bis:</v-list-item-subtitle>
                {{ reservation.reserved_until }}
              </v-list-item>
            </v-list></v-col
          ><v-col
            ><v-list>
              <v-list-item-title>&nbsp;</v-list-item-title>
              <v-list-item>
                <v-list-item-subtitle>Gegenstand:</v-list-item-subtitle>
                {{ reservation.objecttype.name }}
              </v-list-item>
              <v-list-item>
                <v-list-item-subtitle>Anzahl:</v-list-item-subtitle>
                {{ reservation.count }}
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
        <v-select
          v-model="reservation.selectedObjects"
          :items="reservation.selectableObjects"
          multiple
          item-title="merged_identifier"
          item-value="id"
        ></v-select>
      </v-card>
      <v-alert type="warning" v-if="!handleDialog.valid_selection">
        Die ausgewählten Anzahlen passen irgendwo nicht
      </v-alert>
      <div
        v-if="!handleDialog.reservations[0].reserver.verified"
        class="text-red"
      >
        Der Nutzer ist nicht verifiziert, bitte Berechtigung prüfen.
      </div>
      <v-card-actions
        ><v-spacer />
        <!-- enable button if number of selectedObjects equals the count  for each reservation-->
        <v-btn @click="turnReservationsIntoRentals">Speichern</v-btn>
        <v-btn :disabled="!handleDialog.valid_selection" @click="downloadForm"
          >Download Formular</v-btn
        >
        <v-btn
          :disabled="
            !handleDialog.valid_selection ||
            !handleDialog.reservations[0].reserver.verified
          "
          @click="handOutReservations"
          >Verleihen</v-btn
        >
      </v-card-actions></v-card
    >
  </v-dialog>
  <v-dialog v-model="rentals.rentalsDialog.open">
    <v-card class="pa-4">
      <v-checkbox
        v-for="rental in rentals.data.filter(
          (x) =>
            x.grouping1 == rentals.rentalsDialog.relatedItem.grouping1 &&
            x.grouping2 == rentals.rentalsDialog.relatedItem.grouping2 &&
            x.received_back_at == null
        )"
        :key="rental.id"
        :label="rental.merged_identifier"
        :value="rental.id"
        v-model="rentals.rentalsDialog.selectedAsReturned"
      />
      <v-card-actions>
        <v-spacer /><v-btn @click="returnSelectedItems"
          >Rückgabe bestätigen</v-btn
        ></v-card-actions
      >
    </v-card>
  </v-dialog>
</template>
