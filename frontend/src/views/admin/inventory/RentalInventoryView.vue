<script lang="ts">
import { useUserStore } from "@/stores/user";
import QrcodeVue from "qrcode.vue";
import type { RentalObjectTypeType, TagType } from "@/ts/rent.types";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  components: { QrcodeVue },
  data() {
    return {
      qrcodeCanvas: true,
      categories: [],
      objecttypes: {} as RentalObjectTypeType,
      rentalObjectTypes: [] as RentalObjectTypeType[],
      objects: [],
      isCategoryEditDialogOpen: false,
      toBeEditedCategory: {},
      isTypeDetailsDialogOpen: false,
      toBeEditedObjectsType: {},
      suggestions: [],
      selected_suggestions: [],
      openTypeImage: null,
      toBeUploadedImage: null,
      tags: [] as TagType[],
      selectedTags: [],
      deleteDialog: false,
      deleteURL: "",
      deleteData: "",
      duration: {} as { [prioid: number]: { duration: number; id?: number } },
      objectEditData: {},
      objectEditType: "",
      isObjectDetailsDialogOpen: false,
      priorityClasses: [] as {
        id: number;
        name: string;
        description: string;
        prio: number;
      }[],
    };
  },
  async mounted() {
    this.updateData();
  },
  methods: {
    openCreateObjectDialog(localType: string) {
      //calculate highest internal identifier in object array and use it +1 as new value
      const typeObjects = this.objects.filter(
        (object) => object["type"] == localType
      );
      const new_internal_identifier =
        typeObjects.length == 0
          ? 1
          : parseInt(
              typeObjects.sort(
                (object1, object2) =>
                  object2["internal_identifier"] -
                  object1["internal_identifier"]
              )[0]["internal_identifier"]
            ) + 1;
      this.objectEditData["internal_identifier"] = new_internal_identifier + "";
      this.objectEditData["type"] = localType;
      this.isObjectDetailsDialogOpen = true;
    },
    openObjectDetailsDialog(localType) {
      this.objectEditData = { ...localType };
      this.isObjectDetailsDialogOpen = true;
    },
    downloadQrCode() {
      // deepcopy to keep changes to the downloaded file
      let svgContent = document
        .getElementById("qrcode")
        .cloneNode(true) as HTMLElement;
      svgContent.setAttribute("height", "200");
      const width = svgContent.getAttribute("width");
      let textNode = document.createElement("text");
      const textValue = document.createTextNode(
        this.objectEditType + this.objectEditData["internal_identifier"]
      );
      textNode.appendChild(textValue);
      textNode.setAttribute("textLength", width);
      textNode.setAttribute("lengthAdjust", "spacing");
      //TODO fix download and add the name
      //svgContent.appendChild(textNode)
      console.log(svgContent);
      const url = window.URL.createObjectURL(new Blob([svgContent.outerHTML]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        this.objectEditType +
          this.objectEditData["internal_identifier"] +
          ".svg"
      );
      document.body.appendChild(link);
      link.click();
    },
    saveObjectFromDialog(create: boolean) {
      if (
        this.objectEditData["inventory_number"] == "" ||
        this.objectEditData["inventory_number"] == null
      ) {
        delete this.objectEditData["inventory_number"];
      }
      if (create) {
        this.userStore.postURLWithAuth({
          url: "rentalobjects",
          params: this.objectEditData,
        });
      } else {
        this.userStore.patchURLWithAuth({
          url: "rentalobjects/" + this.objectEditData["id"],
          params: this.objectEditData,
        });
      }
      this.isObjectDetailsDialogOpen = false;
      setTimeout(this.updateData, 200);
    },
    async openTypeDetailsDialog(type) {
      console.log(
        await this.userStore.getFromURLWithAuth({
          url: "duration",
          params: { object_type: type.id },
        })
      );
      const duration = await this.userStore.getFromURLWithAuth({
        url: "duration",
        params: { object_type: type.id },
      });
      this.priorityClasses.forEach(
        (prio) => (this.duration[prio.id] = { duration: 0 })
      );
      duration.forEach(
        (x) =>
          (this.duration[x.prio] = { duration: x.duration_in_days, id: x.id })
      );
      console.log(this.duration);
      this.isTypeDetailsDialogOpen = true;
      this.toBeEditedObjectsType = { ...type };
      this.openTypeImage = this.toBeEditedObjectsType["image"];
      //filter all used tags from all possible tags
      this.selectedTags = this.tags.filter((tag) =>
        this.toBeEditedObjectsType["tags"].includes(tag["id"])
      );
      this.suggestions = await this.userStore.getFromURLWithAuth({
        url: "rentalobjecttypes/" + type.id + "/suggestions/",
      });
      this.suggestions.forEach((x) => {
        if (x.suggestion != type.id) {
          this.selected_suggestions.push(x.suggestion);
        }
      });
      this.rentalObjectTypes.forEach((rentaltype) => {
        if (
          this.suggestions.filter(
            (suggestion) => suggestion.suggestion == rentaltype.id
          ).length == 0
        ) {
          this.suggestions.push({
            suggestion: rentaltype.id,
            suggestion_for: type.id,
            description: "",
          });
        }
      });
      console.log(this.suggestions);
    },
    saveEditedObjectsType() {
      let formData = new FormData();
      if (this.openTypeImage.includes("base64")) {
        //string containes 'base64' => uploaded image. because a temporary representation has been set
        formData.append(this.toBeUploadedImage["type"], this.toBeUploadedImage);
      }
      for (const key in this.toBeEditedObjectsType) {
        if (
          Object.prototype.hasOwnProperty.call(
            this.toBeEditedObjectsType,
            key
          ) &&
          key != "rentalobjects"
        ) {
          if (
            key == "image" &&
            !(typeof this.toBeEditedObjectsType[key] == "object")
          ) {
            //since type is not object image has not been changed => shouldnt be uploaded
            continue;
          }
          let element = this.toBeEditedObjectsType[key];

          if (key == "tags" && this.selectedTags.length > 0) {
            // if the tags are selected through the v-select their value is number. if they are not changed they are of type TagType
            element = this.selectedTags.map((x) =>
              typeof x == "number" ? x : x["id"]
            );
          } else if (key == "tags" && this.selectedTags.length == 0) {
            //can not empty many-to-many field with Formdata https://github.com/encode/django-rest-framework/issues/2883
            // so we need a extra request here #cursed
            this.userStore.patchURLWithAuth({
              url: "rentalobjecttypes/" + this.toBeEditedObjectsType["id"],
              params: { tags: [] },
            });
            continue;
          }
          if (Array.isArray(element)) {
            element.forEach((el) => {
              formData.append(key, el);
            });
          } else {
            formData.append(key, element);
          }
        }
      }
      this.userStore
        .patchURLWithAuth({
          url: "rentalobjecttypes/" + this.toBeEditedObjectsType["id"],
          params: formData,
        })
        .then((resp) => {
          if (!String(resp.status).startsWith("2")) {
            return;
          }
          Object.keys(this.duration).forEach((x) => {
            if (
              this.duration[x].duration != "" &&
              this.duration[x].duration != 0
            ) {
              if ("id" in this.duration[x]) {
                //this duration object already exists so patch it not post it
                this.userStore.patchURLWithAuth({
                  url: "duration/" + this.duration[x].id,
                  params: { duration: this.duration[x].duration },
                });
              } else {
                this.userStore.postURLWithAuth({
                  url: "duration",
                  params: {
                    duration: this.duration[x].duration,
                    prio: x,
                    rental_object_type: this.toBeEditedObjectsType["id"],
                  },
                });
              }
            } else if (
              (this.duration[x].duration == "" ||
                this.duration[x].duration == 0) &&
              "id" in this.duration[x]
            ) {
              this.userStore.deleteURLWithAuth({
                url: "duration/" + this.duration[x].id,
              });
            }
          });
          this.userStore.patchURLWithAuth({
            url:
              "rentalobjecttypes/" +
              this.toBeEditedObjectsType["id"] +
              "/suggestions",
            params: this.suggestions.filter((x) =>
              this.selected_suggestions.includes(x.suggestion)
            ),
          });
          this.isTypeDetailsDialogOpen = false;
          setTimeout(this.updateData, 200);
        });
    },
    createEditedObjectsType() {
      // we have to use formdata here, otherwise we couldn't uplaod the image
      let formData = new FormData();
      if (this.openTypeImage != null && this.openTypeImage.includes("base64")) {
        //string containes 'base64' => uploaded image
        formData.append(this.toBeUploadedImage["type"], this.toBeUploadedImage);
      }
      for (const key in this.toBeEditedObjectsType) {
        if (
          Object.prototype.hasOwnProperty.call(
            this.toBeEditedObjectsType,
            key
          ) &&
          key != "rentalobjects"
        ) {
          let element = this.toBeEditedObjectsType[key];

          if (key == "tags" && this.selectedTags.length > 0) {
            element = this.selectedTags.map((x) => x["id"]);
          }
          if (Array.isArray(element)) {
            element.forEach((el) => {
              formData.append(key, el);
            });
          } else {
            formData.append(key, element);
          }
        }
      }
      const response = this.userStore.postURLWithAuth({
        url: "rentalobjecttypes/",
        params: formData,
      });
      response.then((resp) => {
        if (String(resp.status).startsWith("2")) {
          this.isTypeDetailsDialogOpen = false;
          setTimeout(this.updateData, 200);
        } else if (String(resp.status).startsWith("5")) {
          this.userStore.alert(
            "irgendein interner Fehler. Bitte einmal einen Entwickler kontaktieren",
            "warning"
          );
        }
      });
    },
    openCreateTypeDetailsDialog(category: string) {
      this.isTypeDetailsDialogOpen = true;
      this.toBeEditedObjectsType["category"] = category;
    },
    tempSaveTypeImage(e) {
      //temporary save the image as bas64 to display it temporarily
      const image = e.target.files[0];
      this.toBeUploadedImage = image;
      const reader = new FileReader();
      reader.readAsDataURL(image);
      reader.onload = (e) => {
        this.openTypeImage = e.target.result;
      };
      this.toBeEditedObjectsType["image"] = this.toBeUploadedImage;
    },
    async updateData() {
      // use splice to keep reactivity with arrays. Direct array manipulation sometimes does not keep reactivity
      this.tags.splice(
        0,
        this.tags.length,
        ...(await this.userStore.getFromURLWithAuth({ url: "tags" }))
      );
      this.objects.splice(
        0,
        this.objects.length,
        ...(await this.userStore.getFromURLWithAuth({ url: "rentalobjects" }))
      );
      this.categories.splice(
        0,
        this.categories.length,
        ...(await this.userStore.getFromURLWithAuth({ url: "categories" }))
      );
      const types = await this.userStore.getFromURLWithAuth({
        url: "rentalobjecttypes",
      });
      //to reduce network load. load every type and match them on the device
      let resulttypes = {} as RentalObjectTypeType;
      this.categories.forEach((category) => {
        resulttypes[category["id"]] = [];
        types.forEach((objtype) => {
          if (category["id"] == objtype["category"]) {
            resulttypes[category["id"]].splice(
              resulttypes[category["id"]].length,
              0,
              objtype
            );
          }
        });
      });
      this.objecttypes = resulttypes;
      this.rentalObjectTypes = await this.userStore.getFromURLWithAuth({
        url: "rentalobjecttypes",
      });
      console.log(this.rentalObjectTypes);
      this.objects.splice(
        0,
        this.objects.length,
        ...(await this.userStore.getFromURLWithAuth({
          url: "rentalobjects",
        }))
      );
      this.priorityClasses = await this.userStore.getFromURLWithAuth({
        url: "priority",
      });
    },
    /** executes the deletion of an object after the confirmation interface. will delete the object from DATABASE*/
    executeDeletion() {
      this.userStore.deleteURLWithAuth({ url: this.deleteURL });
      this.deleteDialog = false;
      setTimeout(this.updateData, 200);
    },
    createEditedCategory() {
      this.userStore.postURLWithAuth({
        url: "/categories/",
        params: this.toBeEditedCategory,
      });
      this.isCategoryEditDialogOpen = false;
      setTimeout(this.updateData, 200);
    },
    saveEditedCategory() {
      this.userStore.patchURLWithAuth({
        url: "/categories/" + this.toBeEditedCategory["id"],
        params: this.toBeEditedCategory,
      });
      this.isCategoryEditDialogOpen = false;
      setTimeout(this.updateData, 200);
    },
    editCategory(value: number) {
      this.isCategoryEditDialogOpen = true;
      //copy the element to prevent side effects from ref values
      this.toBeEditedCategory = { ...this.categories[value] };
      delete this.toBeEditedCategory["rentalobjecttypes"];
    },
  },
  watch: {
    //delete temp value
    isCategoryEditDialogOpen: function (newvalue) {
      if (!newvalue) {
        this.toBeEditedCategory = {};
      }
    },
    isObjectDetailsDialogOpen: function (newvalue) {
      if (!newvalue) {
        this.objectEditData = {};
        this.objectEditType = "";
      }
    },
    deleteDialog: function (newvalue) {
      if (!newvalue) {
        this.deleteURL = "";
        this.deleteData = "";
      }
    },
    isTypeDetailsDialogOpen: function (newvalue) {
      console.log(this.duration);
      if (!newvalue) {
        this.toBeEditedObjectsType = {};
        this.selectedTags = [];
        this.toBeUploadedImage = "";
        this.openTypeImage = "";
        this.suggestions = [];
        this.selected_suggestions = [];
      }
    },
  },
};
</script>

<template>
  <v-dialog v-model="isObjectDetailsDialogOpen">
    <v-card class="pa-4">
      <template v-slot:title>
        <div class="">
          {{ objectEditType + objectEditData["internal_identifier"] }}
        </div>
        <!--  -->
      </template>
      <v-text-field
        class="ma-2"
        label="Inventarnummer"
        v-model="objectEditData['inventory_number']"
      >
      </v-text-field>
      <v-checkbox
        label="ausleihbar(also z.B. nicht defekt)"
        v-model="objectEditData['rentable']"
      ></v-checkbox>
      <span class="border">
        <v-img>
          <qrcode-vue
            id="qrcode"
            class="ma-2"
            v-if="objectEditData['id']"
            :value="objectEditData['id'] + ''"
            :size="150"
            :render-as="qrcodeCanvas ? 'canvas' : 'svg'"
          ></qrcode-vue
        ></v-img>
        <v-btn
          v-if="!qrcodeCanvas"
          variant="outlined"
          width="200"
          @click="downloadQrCode()"
          >Download Qr-Code</v-btn
        >
        <v-checkbox
          v-model="qrcodeCanvas"
          label="Als Bild rendern"
        ></v-checkbox>
      </span>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click.stop @click="isObjectDetailsDialogOpen = false">
          Abbrechen</v-btn
        >
        <v-btn
          v-if="objectEditData['id']"
          @click.stop
          @click="saveObjectFromDialog(false)"
          :disabled="!userStore.inventory_rights"
        >
          Speichern
        </v-btn>
        <v-btn
          v-else
          @click.stop
          @click="saveObjectFromDialog(true)"
          :disabled="!userStore.inventory_rights"
        >
          Erstellen</v-btn
        >
      </v-card-actions>
    </v-card>
  </v-dialog>
  <v-dialog v-model="isCategoryEditDialogOpen">
    <v-card>
      <v-card-title>
        <v-text-field
          label="Kategoriename"
          v-model="toBeEditedCategory['name']"
        ></v-text-field>
        <v-textarea
          label="Beschreibung"
          v-model="toBeEditedCategory['description']"
        ></v-textarea>
      </v-card-title>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="isCategoryEditDialogOpen = false">Abbrechen</v-btn>
        <template v-if="userStore.inventory_rights">
          <v-btn
            v-if="toBeEditedCategory['id']"
            @click="saveEditedCategory"
            :disabled="!userStore.inventory_rights"
            >Speichern</v-btn
          >
          <v-btn
            v-else
            @click="createEditedCategory"
            :disabled="!userStore.inventory_rights"
            >Erstellen</v-btn
          >
        </template>
      </v-card-actions></v-card
    >
  </v-dialog>
  <!-- Objecttype edit dialog-->
  <v-dialog v-model="isTypeDetailsDialogOpen">
    <v-card class="pa-3">
      <div class="ma-2 text-h4">
        Details von: {{ toBeEditedObjectsType["name"] }}
      </div>
      <v-text-field
        label="Name"
        v-model="toBeEditedObjectsType['name']"
        :readonly="!userStore.inventory_rights"
      ></v-text-field>
      <div class="text-h5 ma-2">
        Die Beschreibung wird in der Detailansicht angezeigt:
      </div>
      <quill-editor
        content-type="html"
        theme="snow"
        :toolbar="userStore.inventory_rights ? 'full' : 'minimal'"
        v-model:content="toBeEditedObjectsType['description']"
        :disabled="!userStore.inventory_rights"
        :readOnly="!userStore.inventory_rights"
      />
      <div class="text-h5 ma-2">
        Die Kurzbeschreibung wird in der Verleihübersicht angezeigt:
      </div>
      <v-textarea
        label="Kurzbeschreibung"
        v-model="toBeEditedObjectsType['shortdescription']"
        :readonly="!userStore.inventory_rights"
      ></v-textarea>
      <v-text-field
        label="Hersteller"
        v-model="toBeEditedObjectsType['manufacturer']"
        :readonly="!userStore.inventory_rights"
      ></v-text-field>
      <v-text-field
        label="Präfix für ID"
        v-model="toBeEditedObjectsType['prefix_identifier']"
        :readonly="!userStore.inventory_rights"
      ></v-text-field>
      <v-select
        v-model:model-value="selectedTags"
        :readonly="!userStore.inventory_rights"
        multiple
        chips
        :items="tags"
        item-title="name"
        item-value="id"
        label="Tags"
      ></v-select>
      <v-checkbox
        label="In Verleihübersicht anzeigen"
        :readonly="!userStore.inventory_rights"
        v-model="toBeEditedObjectsType['visible']"
      ></v-checkbox>
      <v-row>
        <v-avatar class="ma-3" size="100" rounded="0">
          <v-img cover aspect-ratio="1" :src="openTypeImage"></v-img>
        </v-avatar>
        <v-col>
          <v-file-input
            class="mr-3"
            density="compact"
            accept="image/*"
            @change="tempSaveTypeImage"
            v-if="userStore.inventory_rights"
          ></v-file-input>
        </v-col>
      </v-row>
      <div class="border px-3" v-if="'id' in toBeEditedObjectsType">
        <div class="text-h5">Vorschläge</div>
        <!-- show every objecttype as a possible suggestion, but not the item itself-->
        <div>Auswahl der Vorschlagstypen</div>
        <v-select
          v-model="selected_suggestions"
          :items="
            rentalObjectTypes.filter((x) => x.id != toBeEditedObjectsType['id'])
          "
          item-title="name"
          item-value="id"
          multiple
        >
        </v-select>

        <div class="text-h6">Vorschläge und die Verknüpfungen</div>
        <div v-for="suggestion in selected_suggestions" :key="suggestion">
          {{ rentalObjectTypes.find((x) => x.id == suggestion).name
          }}<v-text-field
            label="Beschreibung der Verknüpfung"
            v-model="
              suggestions.find((x) => x.suggestion == suggestion).description
            "
          ></v-text-field>
        </div>
      </div>
      <div class="border pa-3" v-if="'id' in toBeEditedObjectsType">
        <div class="text-h5">Verleihdauern in Tagen</div>
        <div
          v-for="priority in priorityClasses"
          :key="priority.id"
          class="d-flex"
        >
          <v-tooltip activator="parent" location="top">
            {{ priority.description }}
          </v-tooltip>
          <v-text-field
            :label="priority.name + ' (Prio: ' + priority.prio + ')'"
            v-model="duration[priority.id]['duration']"
            type="number"
            :readonly="!userStore.inventory_rights"
            hint="Verleihdauer in Tagen"
          >
            <template #append-inner>Tage</template>
          </v-text-field>
        </div>
      </div>
      <div>
        <v-alert
          v-if="
            userStore.message.alert && !userStore.message.text.includes('html')
          "
          v-model="userStore.message['alert']"
          class="ma-3"
          :type="userStore.message['type']"
          :text="userStore.message['text']"
          closable
        />
      </div>
      <v-card-actions>
        <v-spacer></v-spacer
        ><v-btn @click="isTypeDetailsDialogOpen = false">Schließen</v-btn>
        <template v-if="userStore.inventory_rights">
          <v-btn
            v-if="toBeEditedObjectsType['id']"
            @click="saveEditedObjectsType"
            >Speichern</v-btn
          >
          <v-btn v-else @click="createEditedObjectsType">Erstellen</v-btn>
        </template>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <!-- confirm dialog to delete DB Objects-->
  <v-dialog v-model="deleteDialog">
    <template class="d-flex justify-center">
      <v-card class="pa-3" :class="$vuetify.display.mobile ? 'w-75' : 'w-50'">
        <template v-slot:title
          ><div class="text-h5 font-weight-bold">
            Willst du wirklich das folgende löschen:
          </div></template
        >
        <div class="text-subtitle-2 font-weight-bold">Name:</div>
        <div class="font-italic">{{ deleteData }}</div>

        <template v-slot:actions>
          <v-spacer></v-spacer
          ><v-btn @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn @click="executeDeletion">Löschen</v-btn>
        </template>
      </v-card>
    </template>
  </v-dialog>
  <!-- main part-->
  <div class="d-flex flex-wrap">
    <v-card
      class="w-100 mt-2 mx-2"
      v-for="(category, index) in categories"
      :key="category.id"
    >
      <v-list>
        <v-list-group>
          <template v-slot:activator="{ props }">
            <v-list-item v-bind="props" :subtitle="category.description">
              <template v-slot:title>
                {{ category.name }}
                <v-btn
                  v-if="userStore.inventory_rights"
                  size="small"
                  flat
                  icon="mdi-pencil"
                  @click.stop
                  @click="editCategory(index)"
                ></v-btn>
                <v-btn
                  v-if="userStore.inventory_rights"
                  size="small"
                  flat
                  icon="mdi-delete"
                  @click.stop
                  @click="
                    deleteURL = 'categories/' + category['id'];
                    deleteDialog = !deleteDialog;
                    deleteData = category['name'];
                  "
                ></v-btn>
              </template>
            </v-list-item>
          </template>
          <v-row class="ma-1">
            <v-list-item
              :class="{
                'w-30': !$vuetify.display.mobile,
                'w-100': $vuetify.display.mobile,
              }"
              v-for="rentaltype in objecttypes[categories[index]['id']]"
              :key="rentaltype['id']"
            >
              <v-list-group>
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props" class="type-card">
                    <div class="d-inline-flex">
                      <v-avatar class="ma-3" size="80" rounded="0">
                        <v-img
                          cover
                          aspect-ratio="1"
                          :src="rentaltype['image']"
                        ></v-img>
                      </v-avatar>
                      <div class="flex-column">
                        <v-card-title class="text-xs-h5 d-flex">
                          {{ rentaltype["name"] }}
                        </v-card-title>

                        <v-chip
                          class="ml-4"
                          :color="rentaltype['visible'] ? 'green' : 'red'"
                          :text="
                            rentaltype['visible'] ? 'angezeigt' : 'versteckt'
                          "
                          variant="elevated"
                        ></v-chip>

                        <v-card-actions>
                          <v-btn
                            class="ml-2"
                            variant="outlined"
                            size="small"
                            @click.stop
                            @click="openTypeDetailsDialog(rentaltype)"
                          >
                            Details
                          </v-btn>
                        </v-card-actions>
                      </div>
                    </div>
                  </v-list-item>
                </template>
                <v-list-item
                  v-for="object in objects.filter(
                    (object) => object['type'] == rentaltype['id']
                  )"
                  :key="object['id']"
                >
                  <v-card>
                    <template v-slot:title>
                      {{
                        rentaltype["prefix_identifier"] +
                        object["internal_identifier"]
                      }}
                    </template>
                    <div></div>
                    <v-chip
                      :color="object['rentable'] ? 'green' : 'red'"
                      :text="object['rentable'] ? 'ausleihbar' : 'versteckt'"
                      variant="elevated"
                    ></v-chip>
                    <v-card-actions>
                      <v-btn
                        @click.stop
                        @click="
                          objectEditType = rentaltype['prefix_identifier'];
                          openObjectDetailsDialog(object);
                        "
                        variant="outlined"
                        size="small"
                        >Details</v-btn
                      >
                    </v-card-actions>
                  </v-card>
                </v-list-item>
                <v-list-item v-if="userStore.inventory_rights">
                  <v-btn
                    @click.stop
                    @click="
                      objectEditType = rentaltype['prefix_identifier'];
                      openCreateObjectDialog(rentaltype['id']);
                    "
                    prepend-icon="mdi-plus"
                    action
                    flat
                    >Neues Objekt hinzufügen</v-btn
                  >
                </v-list-item>
              </v-list-group></v-list-item
            >
          </v-row>
          <v-list-item>
            <v-btn
              v-if="userStore.inventory_rights"
              elevation="0"
              prepend-icon="mdi-plus"
              action
              @click.stop
              @click="openCreateTypeDetailsDialog(category.id)"
              >Neuen Typ hinzufügen</v-btn
            >
          </v-list-item>
        </v-list-group>
      </v-list>
    </v-card>
  </div>
  <v-card class="ma-2" v-if="userStore.inventory_rights">
    <v-list>
      <v-list-item>
        <v-btn
          elevation="0"
          prepend-icon="mdi-plus"
          action
          @click.stop
          @click="isCategoryEditDialogOpen = true"
          >Neue Kategorie hinzufügen</v-btn
        >
      </v-list-item>
    </v-list>
  </v-card>
</template>

<style scoped>
.type-card {
  padding: 0 !important;
}

.w-70 {
  width: 60% !important;
}

.titlerow {
  width: inherit;
}
</style>
