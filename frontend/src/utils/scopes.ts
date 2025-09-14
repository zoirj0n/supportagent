export function humanizeScope(scope: string) {
	if (scope.includes("gmail.readonly")) return "Gmail Read-only";
	if (scope.includes("gmail.modify")) return "Gmail Modify";
	if (scope.includes("/userinfo.email") || scope === "email") return "Email Address";
	if (scope.includes("/userinfo.profile") || scope === "profile") return "Basic Profile";
	if (scope === "openid") return "OpenID";
	return scope;
  }

  export const DEFAULT_SCOPES = [
	"https://www.googleapis.com/auth/gmail.modify",
	"https://www.googleapis.com/auth/userinfo.email",
	"https://www.googleapis.com/auth/userinfo.profile",
	"openid",
  ];
