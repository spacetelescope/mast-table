<template>
  <v-alert
    :text="text"
    :icon="icon"
    class="info-box"
    density="compact"
    prominent
    icon-size="default"
  />
</template>

<style>
.info-box {
  background-color: light-dark(#b4dbe9, #013b4d);
  color: light-dark(black, white);
  margin-bottom: 16px;
}
</style>