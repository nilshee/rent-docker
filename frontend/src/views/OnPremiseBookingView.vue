<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { WorkplaceType } from "@/ts/rent.types";
import dateFormat from "dateformat";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  async created() {},
  data() {
    return {
      workplaces: [] as WorkplaceType[],
      infotext: "",
      slots: [],
      days: [],
      dialog: {
        open: false,
        data: {
          comment: "",
          slot_start: null,
          slot_end: null,
          workplace: null,
          user: null,
        },
      },
    };
  },
  mounted() {
    this.updateData();
  },
  watch: {
    "$route.params.id": function (newval) {
      if (typeof newval != "undefined") {
        this.updateData();
      }
    },
  },
  methods: {
    dateFormat: dateFormat,
    updateData() {
      this.userStore
        .getFromURLWithoutAuth({
          url: "workplace",
          params: { displayed: true },
        })
        .then((data) => {
          this.workplaces = data;
        });
      if (
        typeof this.$route.params.id != "undefined" &&
        this.userStore.isLoggedIn
      ) {
        this.userStore
          .getFromURLWithAuth({
            url: "workplace/" + this.$route.params.id + "/slots",
          })
          .then((data) => {
            // copy the slots to a new array and make them distinct
            data.forEach((slot) => {
              this.days.push({ weekday: slot.weekday, date: slot.date });
            });
            //Deduplicate
            this.days = Array.from(new Set(this.days.map((day) => day.date)));
            // format days
            this.days = this.days.map((x) => {
              return { weekday: dateFormat(x, "dddd"), date: x };
            });
            this.slots = data;
          });
      }
    },
    openDialog(start, end) {
      this.dialog.data.slot_start = start;
      this.dialog.data.slot_end = end;
      this.dialog.data.user = this.userStore.user.user.profile["user"];
      this.dialog.data.workplace = this.$route.params.id;
      this.dialog.open = true;
    },
    reserve() {
      this.userStore
        .postURLWithAuth({
          url: "onpremisebooking",
          params: this.dialog.data,
        })
        .then(() => this.updateData());
      this.dialog.open = false;
    },
  },
};
</script>
<template>
  <v-card v-if="typeof $route.params.id == 'undefined'" class="ma-3">
    <v-row>
      <v-col
        v-for="workplace in workplaces"
        :key="workplace.id"
        :cols="$vuetify.display.mobile ? 12 : 4"
      >
        <v-card class="ma-2" :title="workplace.name">
          <v-row class="ml-2">
            <v-col cols="4">
              <v-avatar rounded="0" :size="$vuetify.display.xs ? '150' : '150'">
                <v-img :src="workplace.image" cover aspect-ratio="1" />
              </v-avatar>
            </v-col>
            <v-col class="text-wrap overflow-hidden">
              <v-sheet max-height="150">
                {{ workplace.shortdescription }}
              </v-sheet>
            </v-col>
          </v-row>
          <v-card-actions class="mt-3"
            ><v-spacer /><v-btn
              @click="$router.push('/onpremise/' + workplace.id)"
              >Details</v-btn
            ></v-card-actions
          >
        </v-card>
      </v-col>
    </v-row>
  </v-card>
  <v-card v-else>
    <v-sheet
      v-for="workplace in workplaces.filter(
        (x) => x.id == Number($route.params.id)
      )"
      :key="workplace.id"
    >
      <v-card>
        <v-row>
          <v-col cols="3">
            <v-avatar rounded="0" size="100%">
              <v-img :src="workplace.image" aspect-ratio="1" />
            </v-avatar>
          </v-col>
          <v-col cols="9">
            <v-sheet class="py-5 text-h2">{{ workplace.name }}</v-sheet>
            <hr />
            <div
              class="pa-3 ql-editor ql-snow"
              v-html="workplace.description"
            ></div>
          </v-col>
        </v-row>
        <v-row></v-row>
      </v-card>
      <v-card v-if="userStore.isLoggedIn">
        <v-sheet class="ma-3 text-h6"> </v-sheet>
        <v-table class="ma-2">
          <thead>
            <tr>
              <th v-for="day in days" :key="day.date">
                {{ day.weekday }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td v-for="day in days" :key="day.date">
                <v-sheet
                  :min-width="150"
                  v-for="slot in slots.filter((slo) => slo.date == day.date)"
                  :key="slot.id"
                >
                  <v-btn
                    class="my-2"
                    :disabled="slot.disabled"
                    @click="openDialog(slot.start, slot.end)"
                  >
                    <v-sheet>
                      <v-sheet>
                        {{ dateFormat(slot.start, "isoTime") }} -
                        {{ dateFormat(slot.end, "isoTime") }}
                      </v-sheet>
                      <v-sheet>
                        {{ slot.disabled ? "Blockiert" : "Buchen" }}
                      </v-sheet>
                    </v-sheet>
                  </v-btn>
                </v-sheet>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </v-sheet>
  </v-card>
  <v-dialog v-model="dialog.open">
    <v-card class="pa-3">
      <v-sheet class="text-h5 mb-2">
        Willst du
        {{ workplaces.find((x) => x.id == dialog.data.workplace).name }}
        reservieren?
      </v-sheet>
      <hr />
      <v-sheet>
        Von {{ dateFormat(dialog.data.slot_start, "yyyy-mm-dd HH:MM") }} Bis
        {{ dateFormat(dialog.data.slot_end, "yyyy-mm-dd HH:MM") }}
      </v-sheet>
      <v-textarea
        v-model="dialog.data.comment"
        label="Kommentar zur Reservierung"
      ></v-textarea>
      <v-card-actions
        ><v-spacer /><v-btn @click="reserve">reservieren</v-btn></v-card-actions
      >
    </v-card>
  </v-dialog>
</template>
