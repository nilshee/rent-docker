<script lang="ts">
import { useUserStore } from "@/stores/user";
import type {
  MaxdurationType,
  PriorityType,
  RentalObjectTypeType,
} from "@/ts/rent.types";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  async mounted() {
    this.updateData();
  },
  data() {
    return {
      newPriority: {} as PriorityType,
      priorityClasses: [] as PriorityType[],
      maxDuration: [] as MaxdurationType[],
      objectTypes: [] as RentalObjectTypeType[],
    };
  },
  methods: {
    async updateData() {
      this.priorityClasses = await this.userStore.getFromURLWithAuth({
        url: "priority",
      });

      this.maxDuration = await this.userStore.getFromURLWithAuth({
        url: "duration",
      });

      this.objectTypes = await this.userStore.getFromURLWithAuth({
        url: "rentalobjecttypes",
      });
      this.priorityClasses.forEach((priority) => {
        this.objectTypes.forEach((objectType) => {
          if (
            !this.maxDuration.find(
              (x) =>
                x.rental_object_type == objectType.id && x.prio == priority.id
            )
          ) {
            this.maxDuration.push({
              prio: priority.id,
              duration: 0,
              rental_object_type: objectType.id,
            });
          } else {
            let duration = this.maxDuration.find(
              (x) =>
                x.rental_object_type == objectType.id && x.prio == priority.id
            );
            duration.duration = duration.duration_in_days;
          }
        });
      });
    },
    updatePrio(priority: PriorityType) {
      this.userStore.patchURLWithAuth({
        url: "priority/" + priority.id,
        params: { prio: priority.prio },
      });
    },
    createPriority() {
      if (
        !(
          "name" in this.newPriority &&
          "prio" in this.newPriority &&
          "description" in this.newPriority
        ) ||
        this.newPriority.name == "" ||
        this.newPriority.prio == "" ||
        this.newPriority.prio == 0 ||
        this.newPriority.description == ""
      ) {
        this.userStore.alert("Bitte fülle alle Felder aus", "warning");
      } else {
        this.userStore.postURLWithAuth({
          url: "priority",
          params: this.newPriority,
        });
        this.updateData();
      }
    },
    updateCreateDuration(maxDuration: MaxdurationType) {
      if ("id" in maxDuration) {
        if (maxDuration.duration == "" || maxDuration.duration == 0) {
          this.userStore.deleteURLWithAuth({
            url: "duration/" + maxDuration.id,
          });
        } else {
          delete maxDuration.duration_in_days;
          this.userStore.patchURLWithAuth({
            url: "duration/" + maxDuration.id,
            params: maxDuration,
          });
        }
      } else {
        if (!(maxDuration.duration == "" || maxDuration.duration == 0)) {
          this.userStore.postURLWithAuth({
            url: "duration/",
            params: maxDuration,
          });
        }
      }
    },
    deletePrio(prio: PriorityType) {
      this.userStore.deleteURLWithAuth({ url: "priority/" + prio.id });
      this.updateData();
    },
  },
};
</script>

<template>
  <v-card>
    <v-list>
      <v-list-group v-for="priority in priorityClasses" :key="priority.id">
        <!-- v-list-group opener -->
        <template #activator="{ props }">
          <v-list-item v-bind="props"
            >{{ priority.name + " (Prio: " + priority.prio + ")"
            }}<v-btn
              @click.stop
              @click="deletePrio(priority)"
              icon="mdi-delete"
              flat
            ></v-btn
          ></v-list-item>
        </template>
        <!-- change Priority-->
        <v-list-item>
          <div class="d-flex justify-start">
            <v-text-field
              label="Priorität"
              v-model="priority.prio"
              type="number"
            >
            </v-text-field
            ><v-btn
              class="mx-2 align-center"
              @click.stop
              @click="updatePrio(priority)"
              >UPDATE</v-btn
            >
          </div>
        </v-list-item>
        <!-- type iteration-->
        <v-list-item v-for="objectType in objectTypes" :key="objectType.id">
          <div class="d-flex">
            <v-text-field
              :label="objectType.name"
              v-model="
                maxDuration.find(
                  (x) =>
                    x.rental_object_type == objectType.id &&
                    x.prio == priority.id
                ).duration
              "
            ></v-text-field
            ><v-btn
              class="mx-2 align-center"
              @click.stop
              @click="
                updateCreateDuration(
                  maxDuration.find(
                    (x) =>
                      x.rental_object_type == objectType.id &&
                      x.prio == priority.id
                  )
                )
              "
              >Updaten/Erstellen</v-btn
            >
          </div>
        </v-list-item>
      </v-list-group>
      <!-- Create new Priority Object-->
      <v-list-item title="Neu erstellen"
        ><div class="d-flex">
          <v-text-field class="mx-2" label="Name" v-model="newPriority.name" />
          <v-text-field
            class="mx-2"
            label="Priorität"
            type="number"
            v-model="newPriority.prio"
          />
          <v-btn @click="createPriority()">Erstellen</v-btn>
        </div>
        <v-textarea
          class="mx-2"
          v-model="newPriority.description"
          label="Beschreibung"
        />
      </v-list-item>
    </v-list>
  </v-card>
</template>
