import { threadActionsRegistry } from "@mail/core/common/thread_actions";
import { _t } from "@web/core/l10n/translation";
// import { useComponent } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";
// import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

threadActionsRegistry.add("archive-channel", {
    name: _t("Archive"),
    icon: "fa fa-fw fa-times-circle text-danger",
    iconLarge: "fa fa-fw fa-lg fa-times-circle text-danger",
    sequence: 1,
    sequenceGroup: 100,
    condition(component) {
        return (
            component.thread?.model === "discuss.channel" &&
            (!component.props.chatWindow || component.props.chatWindow.isOpen)
        );
    },
    setup() {
        // This.dialogService = useService("dialog");
        // this.notification = useService("notification");
    },
    async open(component) {
        const thread = component.thread;
        console.log("Channel ID:", thread?.id);
        await component.store.env.services.orm.call(
            "discuss.channel",
            "action_unfollow",
            [thread?.id]
        );
        await component.store.env.services.orm.call(
            "discuss.channel",
            "action_archive",
            [thread?.id]
        );
    },
});

// ThreadActionsRegistry.add("forward-channel", {
//     name: _t("Forward"),
//     icon: "fa fa-fw fa-hand-o-right text-success",
//     iconLarge: "fa fa-fw fa-lg fa-hand-o-right text-success",
//     sequence: 2,
//     sequenceGroup: 100,
//     condition: () => true,
//     setup() {
//         //const component = useComponent();
//         this.notification = useService("notification");
//         this.dialogService = useService("dialog");
//     },
//     async open(component) {
//         // await component.store.env.services.orm.call("discuss.channel", "action_unfollow", [thread?.id]);
//         // await component.store.env.services.orm.call("discuss.channel", "action_archive", [thread?.id]);
//     },
// });
