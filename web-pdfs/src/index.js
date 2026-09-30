// Serves the PDFs to the site (service binding only; this Worker has no public address).
export default {
  fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
