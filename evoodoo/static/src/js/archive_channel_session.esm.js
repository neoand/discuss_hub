import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {_t} from "@web/core/l10n/translation";
import {threadActionsRegistry} from "@mail/core/common/thread_actions";
import {useComponent} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

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
        const component = useComponent();
        component.dialogService = useService("dialog");
    },
    async open(component) {
        const thread = component.thread;
        component.dialogService.add(ConfirmationDialog, {
            body: _t(`Do you want to archive ${thread?.name} ?`),
            title: _t("Archive Channel"),
            confirm: async () => {
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
            cancel: () => {
                return true;
            },
        });
    },
});

threadActionsRegistry.add("forward-channel", {
    name: _t("Forward"),
    icon: "fa fa-fw fa-forward text-info",
    iconLarge: "fa fa-fw fa-lg fa-forward text-info",
    sequence: 2,
    sequenceGroup: 100,
    condition(component) {
        return (
            component.thread?.model === "discuss.channel" &&
            (!component.props.chatWindow || component.props.chatWindow.isOpen)
        );
    },
    setup() {
        const component = useComponent();
        component.dialogService = useService("dialog");
    },
    async open(component) {
        const thread = component.thread;
        component.dialogService.add(FormViewDialog, {
            resModel: "evoodoo.routing_manager",
            title: _t("Forward"),
            context: {
                channel: thread?.id,
            },

            onRecordSaved: async (record) => {
                // If (!record.data.crm_team && !record.data.agent) {
                if (!record.data.agent) {
                    component.env.services.notification.add(
                        _t("Select a user or a team to forward the message!"),
                        {type: "danger"}
                    );
                } else {
                    console.log("AGENT", record.data.agent[0]);

                    // Console.log("TEAM", record.data.crm_team[0])
                    if (record.data.agent) {
                        const user = await component.store.env.services.orm.read(
                            "res.users",
                            [record.data.agent[0]],
                            ["partner_id"]
                        );
                        console.log("USER", user[0].partner_id[0]);
                        await component.store.env.services.orm.call(
                            "discuss.channel",
                            "add_members",
                            [thread?.id],
                            {
                                partner_ids: [user[0].partner_id[0]], // Must be a list, even if it's one partner
                            }
                        );
                    }
                    // Leave the note for context
                    await component.store.env.services.orm.call(
                        "discuss.channel",
                        "message_post",
                        [thread?.id],
                        {
                            // Author_id: userId,
                            body: record.data.note,
                            message_type: "notification",
                        }
                    );
                    // Leave the channel
                    await component.store.env.services.orm.call(
                        "discuss.channel",
                        "action_unfollow",
                        [thread?.id]
                    );
                    component.env.services.notification.add(
                        _t("Message forwarded successfully!"),
                        {type: "success"}
                    );
                }
            },
        });
    },
});
