import SwiftUI

struct AnnotationModePickerView: View {
    @Binding var selection: AnnotationMode

    var body: some View {
        Picker("Annotation Mode", selection: $selection) {
            ForEach(AnnotationMode.allCases) { mode in
                Text(mode.title).tag(mode)
            }
        }
    }
}
