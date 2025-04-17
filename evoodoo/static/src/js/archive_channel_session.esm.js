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
        component.actionService = useService("action");
    },
    async open(component) {
        const thread = component.thread;
        component.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "evoodoo.routing_manager",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_channel_ids: [thread?.id],
            }
        });
    },
});