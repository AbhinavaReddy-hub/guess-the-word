// Same rules as the backend. These only give quick feedback; the server is the real check.
export function checkUsername(username) {
  if (!/^[A-Za-z]{5,30}$/.test(username)) {
    return "Username must be 5 to 30 letters (A-Z, a-z only).";
  }
  return "";
}

export function checkPassword(password) {
  if (password.length < 5 || password.length > 64) return "Password must be 5 to 64 characters.";
  if (!/[A-Za-z]/.test(password)) return "Password must have at least one letter.";
  if (!/\d/.test(password)) return "Password must have at least one number.";
  if (!/[$%*@]/.test(password)) return "Password must have at least one of these: $ % * @";
  return "";
}
