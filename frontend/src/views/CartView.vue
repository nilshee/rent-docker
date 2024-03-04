<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { ReservationPrototypeType } from "@/ts/rent.types";
import Datepicker from "@vuepic/vue-datepicker";
import dateFormat from "dateformat";
import "@vuepic/vue-datepicker/dist/main.css";
export default {
  components: { Datepicker },
  data: () => {
    return {
      attributes: [{ bar: "red", dates: [], format: "yyyy-mm-dd" }],
    };
  },
  async created() {},
  mounted() {},
  methods: {
    refreshMaxDuration() {
      this.userStore.shoppingCart.forEach((thing) => {
        this.userStore
          .getFromURLWithAuth({
            url: "rentalobjecttypes/" + thing.id + "/duration/",
          })
          .then((result) => {
            thing.maxDuration = result["duration_in_days"];
          });
      });
    },

    async validate_and_reserve() {
      let reservation = [];
      let ret = false;
      this.userStore.shoppingCart.forEach((thing) => {
        // check if available has been calculated if not => a date is missing in selection
        if (!("available" in thing)) {
          this.handleDateChange(thing);
          this.userStore.alert(
            "Es muss bei allen Gegenständen ein Zeitraum ausgewählt werden",
            "error"
          );
          return;
        } else {
          if (thing.available.count < thing.count) {
            this.userStore.alert(
              `Es ${thing.available.count > 1 ? "können" : "kann"} maximal${
                thing.available.count > 1 ? "" : " eine"
              } ${thing.available.count} Einheit${
                thing.available.count > 1 ? "en" : ""
              } von ${thing.name} ausgewählt werden`,
              "error"
            );
            thing.count = thing.available.count;
            return;
          } else if (thing.count < 0) {
            this.userStore.alert(
              "Negative Ausleihanzahl? wie soll das denn gehen? Willst du uns was schenken?",
              "warning"
            );
            thing.count = 0;
            return;
          } else if (thing.count == 0) {
            this.userStore.removeFromCart(thing, true);
            this.userStore.alert(
              `Da 0 für ${thing.name} ausgewählt wurde, wurde es aus deinem Warenkorb gelöscht. Bitte überprüfe deine Auswahl und reserviere dann erneut`,
              "warning"
            );
            return;
          }
        }
        reservation.push({
          reserved_from: dateFormat(thing.start, "yyyy-mm-dd"),
          reserved_until: dateFormat(thing.end, "yyyy-mm-dd"),
          objecttype: thing.id,
          count: thing.count,
        });

        ret = true;
      });
      if (!ret) {
        // do not remove stuff from shoppingcart
        return;
      }
      const result = await this.userStore.postURLWithAuth({
        url: "reservations/bulk",
        params: { data: reservation },
      });
      if (
        typeof result != "undefined" &&
        "data" in result &&
        result.data.data.length == this.userStore.shoppingCart.length
      ) {
        this.userStore.alert("erfolgreich reserviert", "success");
      }
      this.userStore.rentRange.end = null;
      this.userStore.available = {};
      this.userStore.shoppingCart = [];
    },
    async handleDateChange(thing) {
      if (thing.end != null && thing.start > thing.end) {
        thing.end = null;
        thing.available = {};
      } else if (thing.end != null && thing.start != null) {
        if (!("available" in thing)) {
          thing.available = {};
          thing.available.start = thing.start;
          thing.available.end = thing.end;
          thing.available.count = (
            await this.userStore.getFromURLWithAuth({
              url: "rentalobjecttypes/" + thing.id + "/available",
              params: {
                from_date: dateFormat(thing.start, "yyyy-mm-dd"),
                until_date: dateFormat(thing.end, "yyyy-mm-dd"),
              },
            })
          )["available"];
        } else if (
          thing.available.start != thing.start ||
          thing.available.end != thing.end
        ) {
          thing.available.start = thing.start;
          thing.available.end = thing.end;
          thing.available.count = (
            await this.userStore.getFromURLWithAuth({
              url: "rentalobjecttypes/" + thing.id + "/available",
              params: {
                from_date: dateFormat(thing.start, "yyyy-mm-dd"),
                until_date: dateFormat(thing.end, "yyyy-mm-dd"),
              },
            })
          )["available"];
        }
        if (thing.available.count < thing.count) {
          thing.count = thing.available.count;
        }
      }
    },
    latestReturningDay(thing: ReservationPrototypeType) {
      // parse start date
      const start = new Date(Date.parse(dateFormat(thing.start)));
      // get theoratical returning day based on maxDuration
      let end = new Date(
        new Date(start).setDate(start.getDate() + thing.maxDuration)
      );
      end.setDate(
        end.getDate() +
          (((Number(this.userStore.settings.returning_day.value) % 7) +
            (7 - end.getDay())) %
            7)
      );
      end.setHours(24, 0, 0, 0);
      //now we diff until next returning day
      return end;
    },
    updatedShoppingCartNumber(thing: ReservationPrototypeType) {
      if (Number(thing.count) <= 0) {
        this.userStore.removeFromCart(thing);
      } else if (Number(thing.count) > thing.available.count) {
        thing.count = thing.available.count;
      }
    },
  },
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  computed: {
    shit() {
      // we fetch it two times, since vue got some problems with it
      this.refreshMaxDuration();
      return this.userStore.shoppingCart;
    },
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
};
</script>

<template>
  <v-card class="ma-2">
    <v-card v-for="thing in shit" :key="thing.id" class="pa-2">
      <v-card flat :title="thing.name">
        <v-avatar class="ma-3" size="80" rounded="0">
          <v-img cover aspect-ratio="1" :src="thing['image']"></v-img>
        </v-avatar>
        Erlaubte Verleihdauer: {{ thing.maxDuration }} Tage
        <div class="d-flex justify-start">
          <div>
            <v-text-field
              class="numberinput"
              variant="outlined"
              type="number"
              v-model="thing.count"
              label="Anzahl"
            >
              <template #append-inner>
                <div>
                  /{{ "available" in thing ? thing.available.count : "?" }}
                </div>
              </template>
              <template #append>
                <v-btn
                  @click="userStore.removeFromCart(thing, true)"
                  color="error"
                  >Löschen</v-btn
                >
              </template>
              <template #prepend>
                <div>Anzahl:</div>
              </template>
            </v-text-field>
          </div>
        </div>
        <v-sheet>
          Bitte wähle den genauen Zeitraum:
        </v-sheet>
        <v-card flat class="d-flex pa-2">
          <datepicker
            auto-apply
            :dark="userStore.theme == 'dark'"
            @internal-model-change="handleDateChange(thing)"
            v-model="thing.start"
            class="mr-2"
            no-disabled-range
            :format="'dd-MM-yyyy'"
            :time-picker="false"
            :min-date="new Date(new Date().setHours(0, 0, 0, 0))"
            :disabled-week-days="disabledLentingWeekdays"
          >
            <template #time-picker><div></div></template>
          </datepicker>
          <datepicker
            auto-apply
            :dark="userStore.theme == 'dark'"
            @internal-model-change="handleDateChange(thing)"
            v-model="thing.end"
            class="mr-2"
            no-disabled-range
            :format="'dd-MM-yyyy'"
            :time-picker="false"
            :min-date="
              new Date(
                new Date(thing.start).setDate(
                  new Date(thing.start).getDate() + 1
                )
              )
            "
            :max-date="latestReturningDay(thing)"
            :disabled-week-days="disabledReturningWeekdays"
          >
            <template #time-picker
              ><div></div
            ></template> </datepicker></v-card></v-card
    ></v-card>
    <v-card-actions v-if="userStore.shoppingCart.length > 0">
      <v-spacer /><v-btn @click="validate_and_reserve()"
        >Verbindlich reservieren</v-btn
      ></v-card-actions
    >
  </v-card>
  <v-card v-if="userStore.shoppingCart.length == 0" class="ma-5 pa-5">
    Bitte gehe zur <router-link to="/">Hauptseite</router-link> und füge
    Gegenstände hinzu
  </v-card>
</template>

<style></style>
