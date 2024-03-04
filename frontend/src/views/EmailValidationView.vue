<script lang="ts">
import { useUserStore } from "@/stores/user";
export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  data() {
    return {
      retData: {} as { success: boolean; detail: string },
    };
  },
  async mounted() {
    let data = new FormData();
    data.append("hash", String(this.$route.params.hash));
    this.retData = (
      await this.userStore.postURLWithoutAuth({
        url: "users/email_validation",
        params: data,
        headers: { "Content-Type": "multipart/form-data" },
      })
    ).data;
  },
};
</script>
<template>
  <v-card>
    <v-container>
      <div>
        {{ retData.success ? "" : "" }}
      </div>
      <div>
        {{ retData.detail }}
      </div>
    </v-container>
  </v-card>
</template>
