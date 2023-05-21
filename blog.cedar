// Admins can perform any action on any resource
permit(
    principal in Role::"admin",
    action,
    resource
);

// Writers can perform post and put on artciles
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
);

// All users can read all resources
permit(
    principal,
    action in Action::"get",
    resource
);