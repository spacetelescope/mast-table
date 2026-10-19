<template>
  <v-alert
    :text="text"
    :icon="icon"
    class="alert"
    density="compact"
    prominent
    icon-size="default"
  />
</template>

<style>
.alert {
  background-color: light-dark(#b4dbe9, #013b4d);
  color: light-dark(black, white);
  margin-bottom: 16px;
}
</style>