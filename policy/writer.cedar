// Writers can perform post and put on artciles
// Add an ABAC enforcement by adding the following statement after the `permit`
// when { principal.karma > 1000 || (context has published  && context.published == false) }
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
);