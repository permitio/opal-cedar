// Admins can perform any action on any resource
permit(
    principal in Role::"admin",
    action,
    resource
);
