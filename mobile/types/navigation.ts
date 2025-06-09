export type RootStackParamList = {
    Menu: undefined;
    Recognize: undefined;
    AddStudent: undefined;
    StudentsList: undefined;
    EditStudent: { student: any };
};

declare global {
    namespace ReactNavigation {
        interface RootParamList extends RootStackParamList {}
    }
}