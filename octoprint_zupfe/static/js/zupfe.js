/*
 * View model for OctoPrint-Zupfe
 *
 * Author: Glenn Hall
 * License: AGPLv3
 */

function timeout(ms) {
    return new Promise((resolve, reject) => {
        setTimeout(resolve, ms);
    });
}

$(function () {

    function ZupfeViewModel(parameters) {


        const self = this;
        self.wizard = parameters[0];
        self.settings = parameters[1];

        // console.log('ZupfeViewModel', self.settings)
        // console.log('ZupfeViewModel', self._bindings[0])

        self.backend_initialized = ko.observable();
        self.backend_connected = ko.observable();
        self.all_bound = ko.observable();
        self.urls = ko.observable();
        self.api_key_invalid = ko.observable();

        // Use knockout since jinja will set staticly the api key
        // but since getting the api key from zupfe is done async
        // maybe the wizard will be shown before the api key is obtained
        self.api_key = ko.observable();

        self.backend_initialized(false);
        self.backend_connected(false);
        self.api_key_invalid(false);
        self.all_bound(false);
        self.api_key(false);
        self.urls({});

        // let pollTimeoutId = setInterval(() => {
        //     console.log(self.settings.settings.plugins.zupfe)
        //     if(self.settings.settings.plugins.zupfe.api_key) {
        //         let api_key = self.settings.settings.plugins.zupfe.api_key();
        //         console.log('APIKEY', api_key)
        //         if (api_key) {
        //             clearInterval(pollTimeoutId);
        //             self.api_key(api_key);
        //         }
        //     }
        // }, 300);


        async function fetch_until_ok(url, options = {}) {
            let response = {ok: false};
            while (!response.ok) {
                response = await fetch(url,
                    {
                        ...options
                    }
                );
                await timeout(300);
            }
            return response.json();
        }

        ;(async () => {
            let urls = await fetch_until_ok('/plugin/zupfe/urls');
            self.urls(urls);
            console.log(urls)
            self.backend_initialized(true);

            let connection = await fetch_until_ok('/plugin/zupfe/connection/status');
            if (connection.status === 'online') {
                self.backend_connected(true);
            }
        })();

        function notify(message, {
            title,
            type = 'success'
        }) {
            // Show a notification.
            new PNotify({
                'title': title,
                'text': message,
                'type': type,
                'hide': true,
                'delay': 10000,
                'mouseReset': true
            });
        }

        self.onDataUpdaterPluginMessage = (plugin, message) => {
            let settingsRoot = $("#settings_plugin_zupfe");
            let navbarRoot = $("#navbar_plugin_zupfe");

            switch (message.type) {
                case EVENT_OCTOPRINT_APIKEY_RECEIVED:
                    self.api_key(message.api_key)
                    break;

                case EVENT_PRINTER_LINKED:
                    self.linked = true;
                    self.wizard.finishWizard();
                    self.wizard.closeDialog();
                    navbarRoot.addClass("zupfe-linked");
                    settingsRoot.addClass("zupfe-linked")
                    notify("Printer linked to ZupFe", {title: "Link"});
                    break;

                case EVENT_PRINTER_UNLINKED:
                    self.linked = false;
                    navbarRoot.removeClass("zupfe-linked");
                    settingsRoot.removeClass("zupfe-linked");
                    notify("Printer unlinked from ZupFe", {title: "Unlink"});
                    break;

                case EVENT_OCTOPRINT_SHOW_WIZARD:
                    self.wizard.showDialog();
                    break;

                case EVENT_OCTOPRINT_BACKEND_INITIALIZED:
                    // self.backend_initialized(true);
                    // self.urls(message.urls);
                    break;

                case EVENT_OCTOPRINT_BACKEND_CONNECTED:
                    self.backend_connected(true);
                    break;

                case EVENT_OCTOPRINT_BACKEND_DISCONNECTED:
                    self.backend_connected(false);
                    break;
            }
        };

        self.onSettingsShown = (...args) => {
            let settingsRoot = $("#settings_plugin_zupfe");
            if (self.linked) {
                settingsRoot.addClass("zupfe-linked")
            } else {
                settingsRoot.removeClass("zupfe-linked")
            }
        };

        self.showSettings = () => {
            self.settings.show("settings_plugin_zupfe");
        };

        self.unlinkPrinter = async () => {
            await fetch('/plugin/zupfe/link', {
                method: 'DELETE'
            })
            // $.ajax(self.urls()[URL_PRINTERS_LINK],
            //     {
            //         type: 'DELETE'
            //     })
        }

        self.onAllBound = () => {
            self.all_bound(true);
            let navbarRoot = $("#navbar_plugin_zupfe");
            self.linked = self.settings.settings.plugins.zupfe.linked();
            self.api_key(self.settings.settings.plugins.zupfe.api_key());
            if (self.linked) {
                navbarRoot.addClass("zupfe-linked")
            }
        };

    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: ZupfeViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["wizardViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_zupfe, #tab_plugin_zupfe, ...
        elements: ["#settings_plugin_zupfe", "#navbar_plugin_zupfe", "#wizard_plugin_zupfe"]
    });
});
