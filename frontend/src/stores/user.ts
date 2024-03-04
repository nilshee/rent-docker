import { defineStore } from "pinia";
import { useStorage } from "@vueuse/core";
import axios, { type AxiosResponse } from "axios";

import type {
  RentalObjectTypeType,
  AvailableType,
  SettingsType,
  ReservationPrototypeType,
  UserStoreType,
} from "@/ts/rent.types";

const apiHost = import.meta.env.VITE_API_HOST;

export const useUserStore = defineStore("user", {
  state: () => ({
    user: useStorage("user", {} as UserStoreType),
    isLoggedIn: false,
    message: { type: "info", text: null, alert: false } as {
      type: "error" | "success" | "warning" | "info";
      text: string;
      alert: boolean;
    },
    shoppingCart: useStorage("shoppingCart", [] as ReservationPrototypeType[]),
    available: {} as AvailableType,
    rentRange: { start: null, end: null, valid: false },
    theme: useStorage("theme", "dark"),
    settings: { onpremise_activated: { value: false } } as SettingsType,
    inventory_rights: false,
    lending_rights: false,
    is_staff: false,
    verificationData: {
      max_refresh_interval: 5,
      url: "",
    } as { url: string; max_refresh_interval: number },
    suggestions: {
      dialogOpen: false,
      data: [],
    },
  }),

  actions: {
    addToCart(objectType: RentalObjectTypeType, openSuggestion = true) {
      //check if this type is already in cart
      if (this.shoppingCart.filter((x) => x.id == objectType.id).length > 0) {
        // increase count by one
        this.shoppingCart.filter((x) => x.id == objectType.id)[0].count++;
      } else {
        //fetch suggestions
        if (openSuggestion) {
          this.openSuggestionsDialog(objectType);
        }

        this.shoppingCart.push({
          ...objectType,
          count: 1,
          start: this.rentRange.start,
          end: null,
        });
      }
    },
    openSuggestionsDialog(objectType: RentalObjectTypeType) {
      this.getFromURLWithAuth({
        url: "rentalobjecttypes/" + objectType["id"] + "/suggestions",
      }).then((data) => {
        if (!this.suggestions.dialogOpen && data.length > 0) {
          this.suggestions.data = data;
          this.suggestions.dialogOpen = true;
        }

        // add type and add count = 1 to the object
      });
    },
    removeFromCart(objectType: RentalObjectTypeType, all?: boolean) {
      if (typeof all != "undefined" && all) {
        this.shoppingCart.find((x) => x.id == objectType.id).count = 1;
      }
      if (this.shoppingCart.find((x) => x.id == objectType.id).count > 1) {
        this.shoppingCart.find((x) => x.id == objectType.id).count--;
      } else {
        const index = this.shoppingCart.indexOf(
          this.shoppingCart.find((x) => x.id == objectType.id)
        );
        this.shoppingCart.splice(index, 1);
      }
    },
    getNumberInCart(objectType: RentalObjectTypeType) {
      if (
        this.shoppingCart.filter((x) => x["id"] == objectType["id"]).length == 0
      ) {
        return 0;
      }
      return this.shoppingCart.filter((x) => x["id"] == objectType["id"])[0]
        .count;
    },
    alert(
      text: string,
      type: "error" | "success" | "warning" | "info",
      duration?: number
    ) {
      this.message["type"] = type;
      this.message["text"] = text;
      this.message["alert"] = true;
      const message = this.message;
      if (typeof duration == "undefined") {
        duration = 4000;
      }
      //display alert for a couple of seconds
      setTimeout(resetAlert, duration);

      function resetAlert() {
        message["alert"] = false;
      }
    },
    /* We shouldn't use post, but we do not have to parse the date before sending if we use post */
    downloadFilledInTemplateWithAuth({ url = "", params = {}, headers = {} }) {
      headers["Authorization"] = "Token " + this.user.token;
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      // if (Object.keys(params).length > 0) {
      //   const urlparams = new URLSearchParams(params);
      //   url += "?" + urlparams.toString();
      // }

      axios({
        url: url,
        data: params,
        method: "POST",
        responseType: "blob",
        headers: headers,
      }).then((response) => {
        const fileURL = window.URL.createObjectURL(new Blob([response.data]));
        const fileLink = document.createElement("a");

        fileLink.href = fileURL;
        fileLink.setAttribute("download", "file.docx");
        document.body.appendChild(fileLink);

        fileLink.click();
      });
    },
    downloadFileWithAuth({ url = "", params = {}, headers = {} }) {
      headers["Authorization"] = "Token " + this.user.token;
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      if (Object.keys(params).length > 0) {
        const urlparams = new URLSearchParams(params);
        url += "?" + urlparams.toString();
      }

      axios({
        url: url,
        data: params,
        method: "GET",
        responseType: "blob",
        headers: headers,
      }).then((response) => {
        const fileURL = window.URL.createObjectURL(new Blob([response.data]));
        const fileLink = document.createElement("a");

        fileLink.href = fileURL;
        fileLink.setAttribute("download", "file.docx");
        document.body.appendChild(fileLink);

        fileLink.click();
      });
    },
    async getFromURLWithoutAuth({ url = "", params = {}, headers = {} }) {
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      if (Object.keys(params).length > 0) {
        const urlparams = new URLSearchParams(params);
        url += "?" + urlparams.toString();
      }

      return await axios
        .get(url, {
          headers: headers,
        })
        .then(function (response) {
          return response.data;
        })
        .catch((error) => {
          let msg = "";
          Object.keys(error["response"]["data"]).forEach(
            (errorkey) => (msg += error["response"]["data"][errorkey])
          );
          this.alert(msg, "warning", 10000);
        });
    },
    async getFromURLWithAuth({ url = "", params = {}, headers = {} }) {
      headers["Authorization"] = "Token " + this.user.token;
      return this.getFromURLWithoutAuth({
        url: url,
        params: params,
        headers: headers,
      });
    },
    async patchURLWithAuth({ url = "", params = {} }): Promise<AxiosResponse> {
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      return await axios
        .patch(url, params, {
          headers: { Authorization: "Token " + this.user.token },
        })
        .then(function (response) {
          return response;
        })
        .catch((error) => {
          let msg = "";
          Object.keys(error["response"]["data"]).forEach(
            (errorkey) => (msg += error["response"]["data"][errorkey])
          );
          this.alert(msg, "warning", 10000);
          return error["response"];
        });
    },
    async deleteURLWithAuth({ url = "" }) {
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      return await axios
        .delete(url, {
          headers: { Authorization: "Token " + this.user.token },
        })
        .then(function (response) {
          return response.data;
        });
    },
    async postURLWithAuth({
      url = "",
      params = {},
      headers = {},
    }): Promise<AxiosResponse> {
      headers["Authorization"] = "Token " + this.user.token;
      return this.postURLWithoutAuth({
        url: url,
        params: params,
        headers: headers,
      });
    },
    async postURLWithoutAuth({
      url = "",
      params = {},
      headers = {},
    }): Promise<AxiosResponse> {
      if (url.slice(0, 1) != "/") {
        url = "/" + url;
      }
      url = apiHost + url;
      if (url.slice(-1) != "/") {
        //strict ending in / is activated in Django
        url += "/";
      }
      return await axios
        .post(url, params, {
          headers: headers,
        })
        .then(function (response) {
          return response;
        })
        .catch((error) => {
          console.log(error);
          let msg = "";
          Object.keys(error["response"]["data"]).forEach(
            (errorkey) =>
              (msg += errorkey + ": " + error["response"]["data"][errorkey])
          );
          this.alert(msg, "warning", 10000);
          return error["reponse"];
        });
    },
    //TODO move to axios + move this.alert
    async signIn(username: string, password: string) {
      if (
        username == "" ||
        password == "" ||
        username.includes(" ") ||
        password.includes(" ")
      ) {
        this.alert(
          "Weder Nutzername noch Passwort darf leer sein oder ein Leerzeichen enthalten",
          "warning"
        );
        return false;
      }
      const res = await fetch(apiHost + "/auth/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });
      const user = await res.json();
      if (res.ok) {
        this.user = user;
        this.alert("Erfolgreich eingeloggt", "success");
        return true;
      } else {
        console.log(user);
      }
      this.alert(user["non_field_errors"][0], "warning");
      return false;
    },
    getReservations({
      open = false,
      unique = false,
      from = null,
      until = null,
      operation_number = null,
    }) {
      let url = apiHost + "/api/reservations/?";

      if (open) {
        url += "open=true&";
      }

      if (unique) {
        url += "unique=true&";
      }

      if (from != null) {
        url += "from=" + from + "&";
      }

      if (operation_number != null) {
        url += "operation_number=" + operation_number + "&";
      }

      if (until != null) {
        url += "until=" + until;
      }

      return axios
        .get(url, { headers: { Authorization: "Token " + this.user.token } })
        .then(function (this, response) {
          this.isLoggedIn = false;
          return response.data;
        });
    },
    async signOut() {
      const res = await fetch(apiHost + "/auth/logout/", {
        method: "POST",
        headers: {
          Authorization: "Token " + this.user.token,
        },
        //body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        this.user = {} as UserStoreType;
        this.isLoggedIn = false;
      }
    },
    async checkCredentials() {
      //check if expiry date is in future return true in that case
      if ("token" in this.user) {
        try {
          const res = await fetch(apiHost + "/auth/checkcredentials/", {
            method: "POST",
            headers: {
              Authorization: "Token " + this.user.token,
            },
            //body: JSON.stringify({ username, password }),
          });
          if (res.status != 200) {
            this.alert(
              "Sie wurden ausgeloggt, bitte loggen Sie sich neu ein.",
              "info"
            );
            this.user = {} as UserStoreType;
            this.isLoggedIn = false;
            this.func_has_inventory_rights();
            this.func_has_lending_rights();
            this.func_isStaff();
            return false;
          }
          this.isLoggedIn = true;
          const user = await res.json();
          this.user.user = user;
          this.func_has_inventory_rights();
          this.func_has_lending_rights();
          this.func_isStaff();
          return true;
        } catch (error) {
          this.user = {} as UserStoreType;
          this.isLoggedIn = false;
          this.func_has_inventory_rights();
          this.func_has_lending_rights();
          this.func_isStaff();
          return false;
        }
      } else {
        this.isLoggedIn = false;
        this.func_has_inventory_rights();
        this.func_has_lending_rights();
        this.func_isStaff();
        return false;
      }
    },
    accountVerification() {
      //helper function for recursive call to check for authorization
      function verify(that, openedWindow) {
        that.postURLWithAuth({ url: "users/oauth/token" }).then((verifyres) => {
          if (
            String(verifyres["status"]).includes("error: authorization pending")
          ) {
            if (openedWindow != null) {
              // spawn a process which will call the api all defined seconds
              setTimeout(
                () => verify(that, openedWindow),
                (that.verificationData.max_refresh_interval + 2) * 1000
              );
            }
          } else {
            that.alert(
              "Dein Account wurde automatisch verifiziert.",
              "success"
            );
            if (openedWindow != null) {
              openedWindow.close();
            }
          }
          if ("automatically_verifiable" in verifyres) {
            that.alert(
              "we couldn't verify you automatically, please verify manually at your first rental"
            );
          }
          //refresh local profile, this will overwrite the verified state
          that.checkCredentials();
        });
      }
      // first we create the verifikation url. this will return {url: "", max_refresh_interval:0} if verification process has already has been finished and there is a access_token.
      this.postURLWithAuth({ url: "users/oauth/verify" }).then((response) => {
        this.verificationData = response.data;
        if (this.verificationData.url != "") {
          // if we receive "", the process has been finished something went wrong
          const openedWindow = window.open(this.verificationData.url, "_blank");
          setTimeout(
            () => verify(this, openedWindow),
            this.verificationData.max_refresh_interval + 2 * 1000
          );
        } else {
          verify(this, null);
        }
      });
    },
    func_isStaff() {
      this.is_staff =
        typeof this.user.user != "undefined" ? this.user.user.is_staff : false;
      return this.is_staff;
    },
    func_has_inventory_rights() {
      this.inventory_rights =
        typeof this.user.user != "undefined"
          ? this.user.user.user_permissions.find(
              (element) => element == "base.inventory_editing"
            ) == "base.inventory_editing"
          : false;
      return this.inventory_rights;
    },
    func_has_lending_rights() {
      this.lending_rights =
        typeof this.user.user != "undefined"
          ? this.user.user.user_permissions.find(
              (element) => element == "base.lending_access"
            ) == "base.lending_access"
          : false;
      return this.lending_rights;
    },
    async refreshSettings() {
      const tempSettings = await this.getFromURLWithoutAuth({
        url: "settings",
      });
      const sortedSettings = {} as SettingsType;
      tempSettings.forEach((x) => {
        if (x.type == "onpremise_activated") {
          sortedSettings.onpremise_activated = {
            value: Boolean(x.value),
            id: x.id,
          };
        } else if (x.type == "onpremise_weekdays") {
          sortedSettings.onpremise_weekdays = {
            value: [x.value.split(",").map((day) => Number(day))],
            id: x.id,
          };
        } else {
          sortedSettings[x.type] = { value: x.value, id: x.id };
        }
      });
      this.settings = sortedSettings;
    },
  },
});
