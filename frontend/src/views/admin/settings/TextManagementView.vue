<script lang="ts">
import { QuillEditor } from "@vueup/vue-quill";
import "@vueup/vue-quill/dist/vue-quill.snow.css";
import "@vueup/vue-quill/dist/vue-quill.bubble.css";
import type { TextType } from "@/ts/rent.types";
import { useUserStore } from "@/stores/user";

import { htmlEditButton } from "quill-html-edit-button";

export default {
  components: { QuillEditor },
  setup() {
    const userStore = useUserStore();
    const quillModules = [
      {
        name: "htmlEditor",
        module: htmlEditButton,
        options: {
          buttonHTML:
            '<svg style="width:24px;height:24px" viewBox="0 0 24 24"><path fill="currentColor" d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M6.12,15.5L9.86,19.24L11.28,17.83L8.95,15.5L11.28,13.17L9.86,11.76L6.12,15.5M17.28,15.5L13.54,11.76L12.12,13.17L14.45,15.5L12.12,17.83L13.54,19.24L17.28,15.5Z" /></svg>',
        },
      },
    ];
    return { userStore, quillModules };
  },
  data() {
    return {
      existentTexts: ["frontpage"],
      texts: [] as TextType[],
    };
  },
  async mounted() {
    this.texts = await this.userStore.getFromURLWithAuth({ url: "texts" });
    const toBeCreatedTexts = this.existentTexts.filter(
      (x) => !this.texts.map((y) => y.name).includes(x)
    );
    if (toBeCreatedTexts.length != 0) {
      toBeCreatedTexts.forEach((x) => {
        this.userStore.postURLWithAuth({
          url: "texts",
          params: { content: "", name: x },
        });
      });
      //refresh texts
      this.texts = await this.userStore.getFromURLWithAuth({ url: "texts" });
    }
  },
  methods: {
    submitText(id: number): void {
      this.userStore.patchURLWithAuth({
        url: "texts/" + String(id),
        params: this.texts.find((text) => text.id == id),
      });
    },
    clearText(text: TextType) {
      this.$refs["editor" + text.id][0].setText("");
    },
  },
};
</script>

<template>
  <v-card class="pa-2">
    <v-expansion-panels>
      <v-expansion-panel v-for="text in texts" :key="text.id">
        <v-expansion-panel-title>
          {{ text.name }}
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div>
            <QuillEditor
              :ref="'editor' + text.id"
              :modules="quillModules"
              theme="snow"
              content-type="html"
              v-model:content="text.content"
              toolbar="full"
            />
          </div>
          <v-btn color="warning" class="mt-2 mr-2" @click="clearText(text)"
            >Leeren</v-btn
          >
          <v-btn color="secondary" class="mt-2" @click="submitText(text.id)"
            >Speichern</v-btn
          ></v-expansion-panel-text
        >
      </v-expansion-panel>
    </v-expansion-panels>
    <!-- <div class="">
      <h3>Content</h3>
      <div class="ql-editor ql-snow" v-html="contentQuill"></div>
    </div> -->
  </v-card>
</template>

<style></style>
