# Proguard rules for Betasan App
-keepattributes *Annotation*
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
-keep class com.betasan.app.data.model.** { *; }
