<script lang="ts">
import { useUserStore } from "@/stores/user";
import type { WorkplaceType, WorkplaceStatusType } from "@/ts/rent.types";
import Datepicker from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
export default {
  components: { Datepicker },
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  created() {},
  data() {
    return {
      workplaces: [] as WorkplaceType[],
      image: null,
      selectedWorkplace: null as WorkplaceType,
      newStatus: {
        reason: "",
        from_date: new Date(),
        until_date: null,
      } as WorkplaceStatusType,
      blockedTimes: [],
      newBlockedTime: { starttime: new Date(), endtime: null },
    };
  },
  mounted() {
    this.updateData();
  },
  watch: {
    selectedWorkplace: function () {
      // if this changes, refresh data to reset unsaved changes
      this.updateData();
      console.log(this.selectedWorkplace);
    },
  },
  methods: {
    uploadImage() {
      console.log(this.image);
      let data = new FormData();
      data.append("image", this.image[0]);
      this.userStore
        .patchURLWithAuth({
          url: "workplace/" + this.selectedWorkplace.id,
          params: data,
        })
        .then(() => this.updateData());
    },
    updateData() {
      this.userStore.getFromURLWithAuth({ url: "workplace" }).then((data) => {
        data.map((x) =>
          x.status.map((stat) => ({
            id: stat.id,
            reason: stat.reason,
            from_date: Date.parse(stat.from_date),
            until_date: Date.parse(stat.until_date),
          }))
        );
        this.workplaces = data;

        console.log(this.workplaces);
      });
      this.userStore
        .getFromURLWithAuth({ url: "onpremiseblockedtimes" })
        .then((data) => (this.blockedTimes = data));
    },
    saveSelectedWorkplace() {
      delete this.selectedWorkplace.image;
      if (!("id" in this.selectedWorkplace)) {
        // not created yet, new Item
        this.userStore
          .postURLWithAuth({ url: "workplace", params: this.selectedWorkplace })
          .then(() => this.updateData());
      } else {
        this.userStore
          .patchURLWithAuth({
            url: "workplace/" + this.selectedWorkplace.id,
            params: this.selectedWorkplace,
          })
          .then(() => this.updateData());
      }
    },
    addNewStatus() {
      let alert = "";
      if (this.newStatus.from_date == null) {
        alert += "Es muss ein Startdatum ausgewählt werden.\n";
      }
      if (this.newStatus.until_date == null) {
        alert += "Es muss ein Endatum ausgewählt werden.\n";
      }
      if (this.newStatus.reason == "") {
        alert += "Es muss eine Begründung ausgewählt werden.";
      }
      if (alert != "") {
        this.userStore.alert(alert, "warning");
      } else {
        this.selectedWorkplace.status.push(this.newStatus);
        this.newStatus = {
          reason: "",
          from_date: new Date(),
          until_date: null,
        };
      }
    },
  },
};
</script>

<template>
  <v-card class="ma-2 pa-2">
    <v-sheet :class="$vuetify.display.mobile ? '' : 'd-flex'">
      <v-select
        :items="workplaces"
        v-model="selectedWorkplace"
        return-object
        item-title="name"
        clearable
      />
      <!-- create a "fake" workplace to work with-->
      <v-btn
        class="ma-3"
        @click="
          selectedWorkplace = {
            name: '',
            shortdescription: '',
            description: '',
            status: [],
            image: '',
            displayed: true,
            exclusions: [],
          }
        "
      >
        Neu erstellen
      </v-btn>
    </v-sheet>

    <v-card v-if="selectedWorkplace != null">
      <v-text-field v-model="selectedWorkplace.name" label="name" />
      <!-- Pictureupload is only possible after the object exists on the remote. this is due to some technical restrictions in the API-->
      <v-sheet class="d-flex" v-if="'id' in selectedWorkplace">
        <v-avatar
          class="ma-2"
          rounded="0"
          :size="$vuetify.display.xs ? '150' : '150'"
        >
          <v-img cover aspect-ratio="1" :src="selectedWorkplace.image"></v-img>
        </v-avatar>
        <v-sheet class="w-100"
          ><v-file-input
            class="mr-3"
            density="compact"
            accept="image/*"
            v-model="image"
            v-if="userStore.inventory_rights"
          /><v-btn
            :disabled="!('id' in selectedWorkplace) || image == null"
            @click="uploadImage()"
            >Bild Hochladen</v-btn
          ></v-sheet
        ></v-sheet
      >
      <v-sheet v-else>
        Ein Bild kann erst nach der Erstellung eines neuen Arbeitsplatzes
        hochgeladen werden.
      </v-sheet>
      <v-sheet class="d-flex">
        <v-checkbox v-model="selectedWorkplace.displayed" label="Anzeigen" />
      </v-sheet>
      <v-textarea
        v-model="selectedWorkplace.shortdescription"
        label="Kurzbeschreibung"
      />
      <v-sheet class="">
        <v-sheet class="text-h6"> Beschreibung: </v-sheet>
        <quill-editor
          content-type="html"
          theme="snow"
          :toolbar="userStore.inventory_rights ? 'full' : 'minimal'"
          v-model:content="selectedWorkplace['description']"
          :disabled="!userStore.inventory_rights"
          :readOnly="!userStore.inventory_rights"
        />
      </v-sheet>
      <v-sheet class="my-3">
        <v-sheet class="text-h6">
          Auswahl von sich ausschließenden Arbeitsplätzen:
        </v-sheet>
        <v-select
          multiple
          label="Arbeitsplätze die nicht gleichzeitig besetzt sein sollten"
          item-title="name"
          item-value="id"
          v-model="selectedWorkplace.exclusions"
          :items="
            workplaces.filter((x) => {
              if ('id' in selectedWorkplace) {
                return x.id != selectedWorkplace.id;
              } else {
                return true;
              }
            })
          "
        />
      </v-sheet>
      <v-expansion-panels>
        <v-expansion-panel title="Statusmeldungen">
          <v-expansion-panel-text>
            <v-table>
              <thead>
                <tr>
                  <th>Begründung</th>
                  <th>Von:</th>
                  <th>Bis:</th>
                  <th>Aktion</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="status in selectedWorkplace.status" :key="status.id">
                  <td>{{ status.reason }}</td>
                  <td>{{ status.from_date }}</td>
                  <td>{{ status.until_date }}</td>
                  <!-- <td><v-btn icon="mdi-delete" flat></v-btn></td> -->
                </tr>
                <tr>
                  <td>
                    <v-text-field
                      variant="underlined"
                      label="Begründung"
                      v-model="newStatus.reason"
                    />
                  </td>
                  <td>
                    <datepicker
                      v-model="newStatus.from_date"
                      :min-date="new Date()"
                    />
                  </td>
                  <td>
                    <datepicker
                      v-model="newStatus.until_date"
                      :min-date="new Date()"
                    />
                  </td>
                  <td><v-btn @click="addNewStatus">Hinzufügen</v-btn></td>
                </tr>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="saveSelectedWorkplace()">{{
          "id" in selectedWorkplace ? "Speichern" : "Erstellen"
        }}</v-btn>
      </v-card-actions></v-card
    >
  </v-card>
  <v-card class="ma-2 pa-3">
    <v-sheet class="text-h5">
      Blockierte Zeiten z.B. niemand ist im Haus
    </v-sheet>
    <v-sheet>
      <v-table>
        <thead>
          <tr>
            <th>Startzeit</th>
            <th>Endzeit</th>
            <th>Aktion</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="block in blockedTimes" :key="block.id">
            <td>
              <datepicker v-model="block.starttime" format="yyyy-MM-dd HH:mm" />
            </td>
            <td>
              <datepicker v-model="block.endtime" format="yyyy-MM-dd HH:mm" />
            </td>
            <td>
              <v-btn
                @click="
                  userStore
                    .patchURLWithAuth({
                      url: 'onpremiseblockedtimes/' + block.id,
                      params: block,
                    })
                    .then((rsp) =>
                      String(rsp.status).startsWith('2')
                        ? userStore.alert('Erfolgreich geändert', 'success')
                        : ''
                    )
                "
                >Speichern</v-btn
              >
              <v-btn
                flat
                icon="mdi-delete"
                @click="
                  userStore
                    .deleteURLWithAuth({
                      url: 'onpremiseblockedtimes/' + block.id,
                    })
                    .then(() => updateData())
                "
              ></v-btn>
            </td>
          </tr>
          <tr>
            <td>
              <datepicker
                v-model="newBlockedTime.starttime"
                format="yyyy-MM-dd HH:mm"
                :min-date="new Date()"
              />
            </td>
            <td>
              <datepicker
                v-model="newBlockedTime.endtime"
                format="yyyy-MM-dd HH:mm"
                :min-date="new Date()"
              />
            </td>
            <td>
              <v-btn
                @click="
                  userStore
                    .postURLWithAuth({
                      url: 'onpremiseblockedtimes/',
                      params: newBlockedTime,
                    })
                    .then((data) => {
                      data.data
                        ? userStore.alert('Erfolgreich geändert', 'success')
                        : '';
                      newBlockedTime = { starttime: new Date(), endtime: null };
                      updateData();
                    })
                "
                >Hinzufügen</v-btn
              >
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-sheet>
  </v-card>
</template>
